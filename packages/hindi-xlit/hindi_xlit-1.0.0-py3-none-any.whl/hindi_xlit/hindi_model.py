import os
import json
import torch
import torch.nn as nn
import numpy as np
from typing import List

# --- GlyphStrawboss ---
class GlyphStrawboss:
    def __init__(self, glyphs='en'):
        if glyphs == 'en':
            self.glyphs = [chr(alpha) for alpha in range(97, 122+1)]
            self.numsym_map = {}
        else:
            self.dossier = json.load(open(glyphs, encoding='utf-8'))
            self.glyphs = self.dossier["glyphs"]
            self.numsym_map = self.dossier["numsym_map"]
        self.char2idx = {}
        self.idx2char = {}
        self._create_index()

    def _create_index(self):
        self.char2idx['_'] = 0  # pad
        self.char2idx['$'] = 1  # start
        self.char2idx['#'] = 2  # end
        self.char2idx['*'] = 3  # mask
        self.char2idx["'"] = 4  # apostrophe
        self.char2idx['%'] = 5  # unused
        self.char2idx['!'] = 6  # unused
        for idx, char in enumerate(self.glyphs):
            self.char2idx[char] = idx + 7
        for char, idx in self.char2idx.items():
            self.idx2char[idx] = char

    def size(self):
        return len(self.char2idx)

    def word2xlitvec(self, word):
        vec = [self.char2idx['$']]
        for i in list(word):
            vec.append(self.char2idx.get(i, self.char2idx['*']))
        vec.append(self.char2idx['#'])
        return np.asarray(vec, dtype=np.int64)

    def xlitvec2word(self, vector):
        char_list = [self.idx2char.get(i, '') for i in vector]
        word = "".join(char_list).replace('$','').replace('#','').replace('_','').replace('*','')
        return word

# --- VocabSanitizer ---
class VocabSanitizer:
    def __init__(self, data_file):
        extension = os.path.splitext(data_file)[-1]
        if extension == ".json":
            self.vocab_set = set(json.load(open(data_file, encoding='utf-8')))
        else:
            raise Exception("Only JSON vocab files are supported.")
    def reposition(self, word_list):
        new_list = []
        temp_ = word_list.copy()
        for v in word_list:
            if v in self.vocab_set:
                new_list.append(v)
                temp_.remove(v)
        new_list.extend(temp_)
        return new_list

# --- Encoder ---
class Encoder(nn.Module):
    def __init__(self, input_dim, embed_dim, hidden_dim,
                 rnn_type='lstm', layers=1, bidirectional=True,
                 dropout=0, device="cpu"):
        super().__init__()
        self.embedding = nn.Embedding(input_dim, embed_dim)
        if rnn_type == "lstm":
            self.enc_rnn = nn.LSTM(embed_dim, hidden_dim, num_layers=layers, bidirectional=bidirectional)
        else:
            raise Exception("Only LSTM is supported.")
    def forward(self, x, x_sz, hidden=None):
        x = self.embedding(x)
        x = x.permute(1,0,2)
        x = nn.utils.rnn.pack_padded_sequence(x, x_sz, enforce_sorted=False)
        output, hidden = self.enc_rnn(x)
        output, _ = nn.utils.rnn.pad_packed_sequence(output)
        output = output.permute(1,0,2)
        return output, hidden

# --- Decoder ---
class Decoder(nn.Module):
    def __init__(self, output_dim, embed_dim, hidden_dim,
                 rnn_type='lstm', layers=2, use_attention=True,
                 enc_outstate_dim=None, dropout=0, device="cpu"):
        super().__init__()
        self.embedding = nn.Embedding(output_dim, embed_dim)
        self.use_attention = use_attention
        self.enc_outstate_dim = enc_outstate_dim if use_attention else 0
        if rnn_type == "lstm":
            self.dec_rnn = nn.LSTM(embed_dim + self.enc_outstate_dim, hidden_dim, num_layers=layers, batch_first=True)
        else:
            raise Exception("Only LSTM is supported.")
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, embed_dim), nn.LeakyReLU(),
            nn.Linear(embed_dim, output_dim),
        )
        if use_attention:
            self.W1 = nn.Linear(self.enc_outstate_dim, hidden_dim)
            self.W2 = nn.Linear(hidden_dim, hidden_dim)
            self.V = nn.Linear(hidden_dim, 1)
    def attention(self, x, hidden, enc_output):
        hidden_with_time_axis = torch.sum(hidden[0], axis=0).unsqueeze(1)
        score = torch.tanh(self.W1(enc_output) + self.W2(hidden_with_time_axis))
        attention_weights = torch.softmax(self.V(score), dim=1)
        context_vector = attention_weights * enc_output
        context_vector = torch.sum(context_vector, dim=1).unsqueeze(1)
        attend_out = torch.cat((context_vector, x), -1)
        return attend_out, attention_weights
    def forward(self, x, hidden, enc_output):
        x = self.embedding(x)
        if self.use_attention:
            x, aw = self.attention(x, hidden, enc_output)
        else:
            aw = 0
        output, hidden = self.dec_rnn(x, hidden)
        output = output.view(-1, output.size(2))
        output = self.fc(output)
        return output, hidden, aw

# --- Seq2Seq ---
class Seq2Seq(nn.Module):
    def __init__(self, encoder, decoder, pass_enc2dec_hid=True, device="cpu"):
        super().__init__()
        self.encoder = encoder
        self.decoder = decoder
        self.device = device
        self.pass_enc2dec_hid = pass_enc2dec_hid
    def active_beam_inference(self, src, beam_width=3, max_tgt_sz=50):
        batch_size = 1
        start_tok = src[0]
        end_tok = src[-1]
        src_sz = torch.tensor([len(src)])
        src_ = src.unsqueeze(0)
        enc_output, enc_hidden = self.encoder(src_, src_sz)
        init_dec_hidden = enc_hidden if self.pass_enc2dec_hid else None
        top_pred_list = [ (0, start_tok.unsqueeze(0), init_dec_hidden) ]
        for t in range(max_tgt_sz):
            cur_pred_list = []
            for p_tup in top_pred_list:
                if p_tup[1][-1] == end_tok:
                    cur_pred_list.append(p_tup)
                    continue
                dec_output, dec_hidden, _ = self.decoder(
                    x=p_tup[1][-1].view(1,1), hidden=p_tup[2], enc_output=enc_output)
                dec_output = nn.functional.log_softmax(dec_output, dim=1)
                pred_topk = torch.topk(dec_output, k=beam_width, dim=1)
                for i in range(beam_width):
                    sig_logsmx_ = p_tup[0] + pred_topk.values[0][i]
                    seq_tensor_ = torch.cat((p_tup[1], pred_topk.indices[0][i].view(1)))
                    cur_pred_list.append((sig_logsmx_, seq_tensor_, dec_hidden))
            cur_pred_list.sort(key=lambda x: x[0], reverse=True)
            top_pred_list = cur_pred_list[:beam_width]
            end_flags_ = [1 if t[1][-1] == end_tok else 0 for t in top_pred_list]
            if beam_width == sum(end_flags_):
                break
        pred_tnsr_list = [t[1] for t in top_pred_list]
        return pred_tnsr_list

# --- XlitPiston ---
class XlitPiston:
    def __init__(self, weight_path, tglyph_cfg_file, iglyph_cfg_file="en", vocab_file=None, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.in_glyph_obj = GlyphStrawboss(iglyph_cfg_file)
        self.tgt_glyph_obj = GlyphStrawboss(glyphs=tglyph_cfg_file)
        if vocab_file:
            self.voc_sanitizer = VocabSanitizer(vocab_file)
        else:
            self.voc_sanitizer = None
        self._numsym_set = set(json.load(open(tglyph_cfg_file, encoding='utf-8'))["numsym_map"].keys())
        self._inchar_set = set("abcdefghijklmnopqrstuvwxyz")
        self._natscr_set = set().union(self.tgt_glyph_obj.glyphs, sum(self.tgt_glyph_obj.numsym_map.values(), []))
        input_dim = self.in_glyph_obj.size()
        output_dim = self.tgt_glyph_obj.size()
        enc_emb_dim = 300
        dec_emb_dim = 300
        enc_hidden_dim = 512
        dec_hidden_dim = 512
        enc_layers = 1
        dec_layers = 2
        enc_bidirect = True
        enc_outstate_dim = enc_hidden_dim * (2 if enc_bidirect else 1)
        enc = Encoder(input_dim, enc_emb_dim, enc_hidden_dim, rnn_type="lstm", layers=enc_layers, bidirectional=enc_bidirect, device=self.device)
        dec = Decoder(output_dim, dec_emb_dim, dec_hidden_dim, rnn_type="lstm", layers=dec_layers, use_attention=True, enc_outstate_dim=enc_outstate_dim, device=self.device)
        self.model = Seq2Seq(enc, dec, pass_enc2dec_hid=True, device=self.device)
        self.model = self.model.to(self.device)
        weights = torch.load(weight_path, map_location=torch.device(self.device))
        self.model.load_state_dict(weights)
        self.model.eval()

    def character_model(self, word, beam_width=1):
        in_vec = torch.from_numpy(self.in_glyph_obj.word2xlitvec(word)).to(self.device)
        p_out_list = self.model.active_beam_inference(in_vec, beam_width=beam_width)
        p_result = [self.tgt_glyph_obj.xlitvec2word(out.cpu().numpy()) for out in p_out_list]
        if self.voc_sanitizer:
            return self.voc_sanitizer.reposition(p_result)
        return p_result

    def inferencer(self, sequence, beam_width=10):
        seg = [sequence]
        lit_seg = []
        p = 0
        while p < len(seg):
            if seg[p][0] in self._natscr_set:
                lit_seg.append([seg[p]])
                p += 1
            elif seg[p][0] in self._inchar_set:
                lit_seg.append(self.character_model(seg[p], beam_width=beam_width))
                p += 1
            elif seg[p][0] in self._numsym_set:
                lit_seg.append([seg[p]])
                p += 1
            else:
                lit_seg.append([seg[p]])
                p += 1
        if len(lit_seg) == 1:
            final_result = lit_seg[0]
        elif len(lit_seg) == 2:
            final_result = [""]
            for seg in lit_seg:
                new_result = []
                for s in seg:
                    for f in final_result:
                        new_result.append(f + s)
                final_result = new_result
        else:
            new_result = []
            for seg in lit_seg:
                new_result.append(seg[0])
            final_result = ["".join(new_result)]
        return final_result 