import sys
import os

sys.path.append('../../../')
sys.path.append('../code')
sys.path.append('../../../python_parser')
import subprocess
import csv
import copy
import json
import argparse
import warnings
import torch
import numpy as np
import random
import bleu
from model import Seq2Seq
from run import TextDataset, InputFeatures, convert_examples_to_features
from utils import select_parents, crossover, map_chromesome, mutate, is_valid_variable_name, _tokenize, \
    get_identifier_posistions_from_code, get_masked_code_by_position, get_substitues, is_valid_substitue, set_seed

from utils import CodeDataset
from utils import getUID, isUID, getTensor, build_vocab, get_code_tokens, is_valid_identifier
from run_parser import get_identifiers, get_example
from torch.utils.data import DataLoader, Dataset, SequentialSampler, RandomSampler,TensorDataset
from transformers import (RobertaForMaskedLM, RobertaConfig, RobertaForSequenceClassification, RobertaTokenizer)

class Example(object):
    """A single training/test example."""

    def __init__(self,
                 idx,
                 source,
                 target,
                 ):
        self.idx = idx
        self.source = source
        self.target = target


def get_new_example(idx, code, nl):
    examples = []
    examples.append(
        Example(idx=idx, source=code, target=nl, )
    )
    return examples

def read_examples(filename):
    """Read examples from filename."""
    examples=[]
    with open(filename,encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line=line.strip()
            js=json.loads(line)
            if 'idx' not in js:
                js['idx']=idx
            else:
                idx = js['idx']
            code=js['code']
            nl=' '.join(js['docstring_tokens']).replace('\n','')
            nl=' '.join(nl.strip().split())
            examples.append(
                Example(
                        idx = idx,
                        source=code,
                        target = nl,
                        )
            )
            # if len(examples) > 1000: break
    return examples

def ids_to_strs(Y, sp):
    ids = []
    eos_id = sp.PieceToId("</s>")
    pad_id = sp.PieceToId("<pad>")
    for idx in Y:
        ids.append(int(idx))
        if int(idx) == eos_id or int(idx) == pad_id:
            break
    return sp.DecodeIds(ids)

def get_transfered_code(code):
    tmp_file = "tmp.json"
    if os.path.exists(tmp_file):
        os.remove(tmp_file)
    jar_path = "StyleTransformer.jar"
    execute = "java -jar {} '{}'".format(jar_path, code)
    output = subprocess.Popen(execute, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    res = output.stdout.readlines()
    adv_codes = []
    try:
        with open(tmp_file) as f:
            for line in f:
                line = line.strip()
                js = json.loads(line)
                adv_codes = js["adv_codes"]
        os.remove(tmp_file)
        return adv_codes
    except:
        # print("file not exists.")
        return adv_codes


class ALERT_Attacker():
    def __init__(self, args, model_tgt, tokenizer_tgt, tokenizer_mlm, bleu_file) -> None:
        self.args = args
        self.model_tgt = model_tgt
        self.tokenizer_tgt = tokenizer_tgt
        self.tokenizer_mlm = tokenizer_mlm
        self.bleu_file = bleu_file
        self.query = 0

    def eval_bleu(self, example):
        self.query += 1
        bleu_file = self.bleu_file
        model = self.model_tgt
        tokenizer = self.tokenizer_tgt
        eval_features = convert_examples_to_features([example], tokenizer, self.args, stage='test')
        eval_data = TextDataset(eval_features, self.args)

        # Calculate bleu
        eval_sampler = SequentialSampler(eval_data)
        eval_dataloader = DataLoader(eval_data, sampler=eval_sampler, batch_size=self.args.eval_batch_size)

        model.eval()
        p = []
        for batch in eval_dataloader:
            batch = tuple(t.to(self.args.device) for t in batch)
            source_ids, target_ids, source_mask, target_mask = batch
            with torch.no_grad():
                preds = model(source_ids=source_ids, source_mask=source_mask)
                for pred in preds:
                    t = pred[0].cpu().numpy()
                    t = list(t)
                    if 0 in t:
                        t = t[:t.index(0)]
                    text = ids_to_strs(t, tokenizer)
                    p.append(text)
        pre_summary = p[0]
        model.train()
        predictions = []
        if os.path.exists(bleu_file + "/dev.output"):
            os.remove(bleu_file + "/dev.output")
        if os.path.exists(bleu_file + "/dev.gold"):
            os.remove(bleu_file + "/dev.gold")
        with open((bleu_file + "/dev.output"), 'w') as f, open((bleu_file + "/dev.gold"), 'w') as f1:
            for ref, gold in zip(p, [example]):
                predictions.append(str(gold.idx) + '\t' + ref)
                f.write(str(gold.idx) + '\t' + ref + '\n')
                f1.write(str(gold.idx) + '\t' + gold.target + '\n')
        f.close()
        f1.close()
        try:
            (goldMap, predictionMap) = bleu.computeMaps(predictions, bleu_file + "/dev.gold")
            dev_bleu = round(bleu.bleuFromMaps(goldMap, predictionMap)[0], 2)
        except:
            dev_bleu = -1

        return dev_bleu, pre_summary, example.target

    def compute_fitness(self, idx, nl, chromesome, orig_prob, code):
        # 计算fitness function.
        # words + chromesome + orig_label + current_prob
        temp_code = map_chromesome(chromesome, code, "java")
        new_example = get_new_example(idx, temp_code, nl)
        new_bleu, _, _ = self.eval_bleu(new_example[0])

        fitness_value = orig_prob - new_bleu
        return fitness_value

    def get_importance_score(self, idx, nl, code, current_prob, words_list: list, variable_names: list):
        '''Compute the importance score of each variable'''
        # label: example[1] tensor(1)
        # 1. 过滤掉所有的keywords.
        positions = get_identifier_posistions_from_code(words_list, variable_names)
        # 需要注意大小写.
        if len(positions) == 0:
            ## 没有提取出可以mutate的position
            return None, None, None

        new_bleus = []

        # 2. 得到Masked_tokens
        masked_token_list, replace_token_positions = get_masked_code_by_position(words_list, positions)
        # replace_token_positions 表示着，哪一个位置的token被替换了.

        for index, tokens in enumerate([words_list] + masked_token_list):
            new_code = ' '.join(tokens)
            new_example = get_new_example(idx, new_code, nl)
            new_bleu, _, _ = self.eval_bleu(new_example[0])
            new_bleus.append(new_bleu)

        importance_score = []
        for new_bleu in new_bleus:
            importance_score.append(current_prob - new_bleu)

        return importance_score, replace_token_positions, positions

    def filter_identifier(self, code, identifiers):
        code_token = get_code_tokens(code)
        filter_identifiers = []
        for identifier in identifiers:
            if is_valid_identifier(identifier):
                position = []
                for index, token in enumerate(code_token):
                    if identifier == token:
                        position.append(index)
                if not all(x > self.args.max_source_length-2 for x in position):
                    filter_identifiers.append(identifier)
        return filter_identifiers

    def ga_attack(self, current_prob, example, substitutions, code, initial_replace=None):
    # def ga_attack(self, example, substituions, code, initial_replace=None):

        # Start the attack
        code = example.source
        pre = None
        idx = example.idx
        nl = example.target
        original_bleu = current_prob
        identifiers, code_tokens = get_identifiers(code, 'java')
        prog_length = len(code_tokens)
        processed_code = " ".join(code_tokens)
        words, sub_words, keys = _tokenize(processed_code, self.tokenizer_mlm)
        variable_names = list(substitutions.keys())
        variable_names = self.filter_identifier(code, variable_names)

        adv_code = ''
        names_positions_dict = get_identifier_posistions_from_code(words, variable_names)

        nb_changed_var = 0  # 表示被修改的variable数量
        nb_changed_pos = 0
        is_success = -1

        # 我们可以先生成所有的substitues
        variable_substitue_dict = {}

        for tgt_word in names_positions_dict.keys():
            all_substitues = substitutions[tgt_word]
            all_substitues = [subs.strip() for i, subs in enumerate(all_substitues) if i < 15]
            variable_substitue_dict[tgt_word] = all_substitues

        if len(variable_substitue_dict) == 0:
            is_success = -3
            return is_success, adv_code, None, nb_changed_var, nb_changed_pos, None

        fitness_values = []
        base_chromesome = {word: word for word in variable_substitue_dict.keys()}
        population = [base_chromesome]
        # 关于chromesome的定义: {tgt_word: candidate, tgt_word_2: candidate_2, ...}
        for tgt_word in variable_substitue_dict.keys():
            # 这里进行初始化
            if initial_replace is None:
                # 对于每个variable: 选择"影响最大"的substitues
                pred_list = []
                substitute_list = []

                most_gap = 0.0
                initial_candidate = tgt_word
                tgt_positions = names_positions_dict[tgt_word]

                # 原来是随机选择的，现在要找到改变最大的.
                for a_substitue in variable_substitue_dict[tgt_word]:
                    # a_substitue = a_substitue.strip()

                    substitute_list.append(a_substitue)
                    # 记录下这次换的是哪个substitue
                    temp_code = get_example(code, tgt_word, a_substitue, "java")
                    new_example = get_new_example(idx, temp_code, nl)
                    pred = self.eval_bleu(new_example[0])
                    pred_list.append(pred)

                if len(pred_list) == 0:
                    # 并没有生成新的mutants，直接跳去下一个token
                    continue
                _the_best_candidate = -1
                for index, pred in enumerate(pred_list):
                    gap = current_prob - pred[0]
                    # 并选择那个最大的gap.
                    if gap > most_gap:
                        most_gap = gap
                        _the_best_candidate = index
                if _the_best_candidate == -1:
                    initial_candidate = tgt_word
                else:
                    initial_candidate = substitute_list[_the_best_candidate]
            else:
                initial_candidate = initial_replace[tgt_word]

            temp_chromesome = copy.deepcopy(base_chromesome)
            temp_chromesome[tgt_word] = initial_candidate
            population.append(temp_chromesome)
            temp_fitness = self.compute_fitness(idx, nl, temp_chromesome, original_bleu, code)
            fitness_values.append(temp_fitness)

        cross_probability = 0.7

        max_iter = max(5 * len(population), 10)
        # 这里的超参数还是的调试一下.

        for i in range(max_iter):
            _temp_mutants = []
            for j in range(64):
                p = random.random()
                chromesome_1, index_1, chromesome_2, index_2 = select_parents(population)
                if p < cross_probability:  # 进行crossover
                    if chromesome_1 == chromesome_2:
                        child_1 = mutate(chromesome_1, variable_substitue_dict)
                        continue
                    child_1, child_2 = crossover(chromesome_1, chromesome_2)
                    if child_1 == chromesome_1 or child_1 == chromesome_2:
                        child_1 = mutate(chromesome_1, variable_substitue_dict)
                else:  # 进行mutates
                    child_1 = mutate(chromesome_1, variable_substitue_dict)
                _temp_mutants.append(child_1)

            # compute fitness in batch
            pred_list = []
            for mutant in _temp_mutants:
                _temp_code = map_chromesome(mutant, code, "java")
                new_example = get_new_example(idx, _temp_code, nl)
                pred = self.eval_bleu(new_example[0])
                pred_list.append(pred)
            if len(pred_list) == 0:
                continue
            mutate_fitness_values = []
            for index, pred in enumerate(pred_list):
                pre = pred[1]
                adv_code = map_chromesome(_temp_mutants[index], code, "java")
                if pred[0] == 0.0:
                    is_success = 1
                    replaced_words = {key: val for key, val in _temp_mutants[index].items() if key != val}
                    for tmp_token in code_tokens:
                        if tmp_token in replaced_words.keys():
                            nb_changed_pos += 1

                    return is_success, adv_code, pred[1], len(replaced_words), nb_changed_pos, replaced_words

                _tmp_fitness = original_bleu - pred[0]
                mutate_fitness_values.append(_tmp_fitness)

            # 现在进行替换.
            for index, fitness_value in enumerate(mutate_fitness_values):
                min_value = min(fitness_values)
                if fitness_value > min_value:
                    # 替换.
                    min_index = fitness_values.index(min_value)
                    population[min_index] = _temp_mutants[index]
                    fitness_values[min_index] = fitness_value

        return is_success, adv_code, pre, None, None, None

    def greedy_attack(self, current_prob, example, substitutions, code):
        '''
        return
            original program: code
            program length: prog_length
            adversar program: adv_program
            true label: true_label
            original prediction: orig_label
            adversarial prediction: temp_label
            is_attack_success: is_success
            extracted variables: variable_names
            importance score of variables: names_to_importance_score
            number of changed variables: nb_changed_var
            number of changed positions: nb_changed_pos
            substitues for variables: replaced_words
        '''
        # Start the attack
        code = example.source
        idx = example.idx
        nl = example.target
        original_bleu = current_prob
        identifiers, code_tokens = get_identifiers(code, 'java')
        prog_length = len(code_tokens)
        processed_code = " ".join(code_tokens)
        words, sub_words, keys = _tokenize(processed_code, self.tokenizer_mlm)
        variable_names = list(substitutions.keys())
        variable_names = self.filter_identifier(code, variable_names)

        adv_code = ''

        # 计算importance_score.
        importance_score, replace_token_positions, names_positions_dict = self.get_importance_score(idx, nl, code, current_prob,
                                                                                               words, variable_names)

        if importance_score is None:
            return -1, None, None, None, None, None

        token_pos_to_score_pos = {}

        for i, token_pos in enumerate(replace_token_positions):
            token_pos_to_score_pos[token_pos] = i
        # 重新计算Importance score，将所有出现的位置加起来（而不是取平均）.
        names_to_importance_score = {}

        for name in names_positions_dict.keys():
            total_score = 0.0
            positions = names_positions_dict[name]
            for token_pos in positions:
                # 这个token在code中对应的位置
                # importance_score中的位置：token_pos_to_score_pos[token_pos]
                total_score += importance_score[token_pos_to_score_pos[token_pos]]

            names_to_importance_score[name] = total_score

        sorted_list_of_names = sorted(names_to_importance_score.items(), key=lambda x: x[1], reverse=True)
        # 根据importance_score进行排序

        final_words = copy.deepcopy(words)
        final_code = copy.deepcopy(code)
        nb_changed_var = 0  # 表示被修改的variable数量
        nb_changed_pos = 0
        is_success = -1
        replaced_words = {}
        query_times = 0
        for name_and_score in sorted_list_of_names:
            tgt_word = name_and_score[0]
            tgt_positions = names_positions_dict[tgt_word]

            all_substitues = substitutions[tgt_word]

            # 得到了所有位置的substitue，并使用set来去重

            most_gap = 0.0
            candidate = None
            replace_examples = []

            substitute_list = []
            pred_list = []
            # 依次记录了被加进来的substitue
            # 即，每个temp_replace对应的substitue.

            all_substitues = [subs.strip() for i, subs in enumerate(all_substitues) if i < 15]
            for substitute in all_substitues:
                # temp_replace = copy.deepcopy(final_words)
                # for one_pos in tgt_positions:
                #     temp_replace[one_pos] = substitute

                substitute_list.append(substitute)
                # 记录了替换的顺序

                # 需要将几个位置都替换成sustitue_
                temp_code = get_example(final_code, tgt_word, substitute, "java")

                new_example = get_new_example(idx, temp_code, nl)
                pred = self.eval_bleu(new_example[0])
                pred_list.append(pred)
            for index, pred in enumerate(pred_list):
                # print("adv_bleu: {}, original_bleu: {}".format(pred[0], original_bleu))
                if pred[0] == 0.0:
                    is_success = 1
                    candidate = substitute_list[index]
                    replaced_words[tgt_word] = candidate
                    adv_code = get_example(final_code, tgt_word, candidate, "java")
                    print("%s SUC! %s => %s (%.5f => %.5f)" % \
                          ('>>', tgt_word, candidate,
                           current_prob, pred[0]), flush=True)
                    replaced_words = {key: val for key, val in replaced_words.items() if key != val}
                    for tmp_token in code_tokens:
                        if tmp_token in replaced_words.keys():
                            nb_changed_pos += 1
                    return is_success, adv_code, pred[1], len(replaced_words), nb_changed_pos, replaced_words
                else:
                    # 如果没有攻击成功，我们看probability的修改
                    gap = current_prob - pred[0]
                    # 并选择那个最大的gap.
                    if gap > most_gap:
                        most_gap = gap
                        candidate = substitute_list[index]

            if most_gap > 0:

                nb_changed_var += 1
                nb_changed_pos += len(names_positions_dict[tgt_word])
                current_prob = current_prob - most_gap
                replaced_words[tgt_word] = candidate
                final_code = get_example(final_code, tgt_word, candidate, "java")
                print("%s ACC! %s => %s (%.5f => %.5f)" % \
                      ('>>', tgt_word, candidate,
                       current_prob + most_gap,
                       current_prob), flush=True)
            else:
                replaced_words[tgt_word] = tgt_word

            adv_code = final_code

        return is_success, adv_code, pred[1], nb_changed_var, nb_changed_pos, replaced_words

class Style_Attacker():
    def __init__(self, args, model_tgt, tokenizer_tgt, bleu_file) -> None:
        self.bleu_file = bleu_file
        self.query = 0
        self.args = args
        self.model_tgt = model_tgt
        self.tokenizer_tgt = tokenizer_tgt

    def eval_bleu(self, example):
        self.query += 1
        bleu_file = self.bleu_file
        model = self.model_tgt
        tokenizer = self.tokenizer_tgt
        eval_features = convert_examples_to_features([example], tokenizer, self.args, stage='test')
        eval_data = TextDataset(eval_features, self.args)

        # Calculate bleu
        eval_sampler = SequentialSampler(eval_data)
        eval_dataloader = DataLoader(eval_data, sampler=eval_sampler, batch_size=self.args.eval_batch_size)

        model.eval()
        p = []
        for batch in eval_dataloader:
            batch = tuple(t.to(self.args.device) for t in batch)
            source_ids, target_ids, source_mask, target_mask = batch
            with torch.no_grad():
                preds = model(source_ids=source_ids, source_mask=source_mask)
                for pred in preds:
                    t = pred[0].cpu().numpy()
                    t = list(t)
                    if 0 in t:
                        t = t[:t.index(0)]
                    text = ids_to_strs(t, tokenizer)
                    p.append(text)
        pre_summary = p[0]
        model.train()
        predictions = []
        if os.path.exists(bleu_file + "/dev.output"):
            os.remove(bleu_file + "/dev.output")
        if os.path.exists(bleu_file + "/dev.gold"):
            os.remove(bleu_file + "/dev.gold")
        with open((bleu_file + "/dev.output"), 'w') as f, open((bleu_file + "/dev.gold"), 'w') as f1:
            for ref, gold in zip(p, [example]):
                predictions.append(str(gold.idx) + '\t' + ref)
                f.write(str(gold.idx) + '\t' + ref + '\n')
                f1.write(str(gold.idx) + '\t' + gold.target + '\n')
        f.close()
        f1.close()
        try:
            (goldMap, predictionMap) = bleu.computeMaps(predictions, bleu_file + "/dev.gold")
            dev_bleu = round(bleu.bleuFromMaps(goldMap, predictionMap)[0], 2)
        except:
            dev_bleu = -1

        return dev_bleu, pre_summary, example.target

    def style_attack(self, original_bleu, example, adv_codes, query_times):
        is_success = -1
        min_preds = 1000.0
        final_code = []
        final_sum = ''
        adv_codes1 = []
        adv_codes2 = []
        code = example.source
        for adv_code in adv_codes:
            new_example = get_new_example(example.idx, adv_code, example.target)
            pred = self.eval_bleu(new_example[0])
            query_times += 1
            if pred[0] == 0.0:
                is_success = 1
                print("%s SUC! (%.5f => %.5f)" % \
                      ('>>', original_bleu, pred[0]), flush=True)
                return is_success, final_code, adv_code, pred[1], query_times
            else:
                if pred[0] < min_preds:
                    min_preds = pred[0]
                    final_code = adv_code
                    final_sum = pred[1]
            if query_times >= 15:
                return is_success, final_code, adv_code, final_sum, query_times

        for adv_code in adv_codes:
            new_adv_codes = get_transfered_code(adv_code)
            adv_codes1 += new_adv_codes
            if query_times + len(adv_codes1) >= 15:
                break

        for adv_code1 in adv_codes1:
            new_example = get_new_example(example.idx, adv_code1, example.target)
            pred = self.eval_bleu(new_example[0])
            query_times += 1
            if pred[0] == 0.0:
                is_success = 1
                print("%s SUC! (%.5f => %.5f)" % \
                      ('>>', original_bleu, pred[0]), flush=True)
                return is_success, final_code, adv_code1, pred[1], query_times
            else:
                if pred[0] < min_preds:
                    min_preds = pred[0]
                    final_code = adv_code1
                    final_sum = pred[1]

            if query_times >= 15:
                return is_success, final_code, adv_code1, final_sum, query_times

        for adv_code1 in adv_codes1:
            new_adv_codes = get_transfered_code(adv_code1)
            adv_codes2 += new_adv_codes
            if query_times + len(adv_codes2) >= 15:
                break

        return is_success, final_code, adv_codes2, final_sum, query_times

class WIR_Attacker():
    def __init__(self, args, model_tgt, tokenizer_tgt, _token2idx, _idx2token, bleu_file) -> None:
        self.model_tgt = model_tgt
        self.tokenizer_tgt = tokenizer_tgt
        self.token2idx = _token2idx
        self.idx2token = _idx2token
        self.args = args
        self.bleu_file = bleu_file
        self.query = 0

    def eval_bleu(self, example):
        self.query += 1
        bleu_file = self.bleu_file
        model = self.model_tgt
        tokenizer = self.tokenizer_tgt
        eval_features = convert_examples_to_features([example], tokenizer, self.args, stage='test')
        eval_data = TextDataset(eval_features, self.args)

        # Calculate bleu
        eval_sampler = SequentialSampler(eval_data)
        eval_dataloader = DataLoader(eval_data, sampler=eval_sampler, batch_size=self.args.eval_batch_size)

        model.eval()
        p = []
        for batch in eval_dataloader:
            batch = tuple(t.to(self.args.device) for t in batch)
            source_ids, target_ids, source_mask, target_mask = batch
            with torch.no_grad():
                preds = model(source_ids=source_ids, source_mask=source_mask)
                for pred in preds:
                    t = pred[0].cpu().numpy()
                    t = list(t)
                    if 0 in t:
                        t = t[:t.index(0)]
                    text = ids_to_strs(t, tokenizer)
                    p.append(text)
        pre_summary = p[0]
        model.train()
        predictions = []
        if os.path.exists(bleu_file + "/dev.output"):
            os.remove(bleu_file + "/dev.output")
        if os.path.exists(bleu_file + "/dev.gold"):
            os.remove(bleu_file + "/dev.gold")
        with open((bleu_file + "/dev.output"), 'w') as f, open((bleu_file + "/dev.gold"), 'w') as f1:
            for ref, gold in zip(p, [example]):
                predictions.append(str(gold.idx) + '\t' + ref)
                f.write(str(gold.idx) + '\t' + ref + '\n')
                f1.write(str(gold.idx) + '\t' + gold.target + '\n')
        f.close()
        f1.close()
        try:
            (goldMap, predictionMap) = bleu.computeMaps(predictions, bleu_file + "/dev.gold")
            dev_bleu = round(bleu.bleuFromMaps(goldMap, predictionMap)[0], 2)
        except:
            dev_bleu = -1

        return dev_bleu, pre_summary, example.target

    def filter_identifier(self, code, identifiers):
        code_token = get_code_tokens(code)
        filter_identifiers = []
        for identifier in identifiers:
            if is_valid_identifier(identifier):
                position = []
                for index, token in enumerate(code_token):
                    if identifier == token:
                        position.append(index)
                if not all(x > self.args.max_source_length - 2 for x in position):
                    filter_identifiers.append(identifier)
        return filter_identifiers

    def get_importance_score(self, idx, nl, code, current_prob, words_list: list, variable_names: list):
        '''Compute the importance score of each variable'''
        # label: example[1] tensor(1)
        # 1. 过滤掉所有的keywords.
        positions = get_identifier_posistions_from_code(words_list, variable_names)
        # 需要注意大小写.
        if len(positions) == 0:
            ## 没有提取出可以mutate的position
            return None, None, None

        new_bleus = []

        # 2. 得到Masked_tokens
        masked_token_list, replace_token_positions = get_masked_code_by_position(words_list, positions)
        # replace_token_positions 表示着，哪一个位置的token被替换了.

        for index, tokens in enumerate([words_list] + masked_token_list):
            new_code = ' '.join(tokens)
            new_example = get_new_example(idx, new_code, nl)
            new_bleu, _, _ = self.eval_bleu(new_example[0])
            new_bleus.append(new_bleu)

        importance_score = []
        for new_bleu in new_bleus:
            importance_score.append(current_prob - new_bleu)

        return importance_score, replace_token_positions, positions

    def wir_random_attack(self, current_prob, example):
        # Start the attack
        code = example.source
        idx = example.idx
        nl = example.target
        original_bleu = current_prob
        identifiers, code_tokens = get_identifiers(code, 'java')
        prog_length = len(code_tokens)
        processed_code = " ".join(code_tokens)
        words, sub_words, keys = _tokenize(processed_code, self.tokenizer_tgt)
        variable_names = [identifier[0] for identifier in identifiers]
        variable_names = self.filter_identifier(code, variable_names)

        adv_code = ''

        # 计算importance_score.
        importance_score, replace_token_positions, names_positions_dict = self.get_importance_score(idx, nl, code,
                                                                                               current_prob,
                                                                                               words, variable_names)

        if importance_score is None:
            return -1, None, None, None, None, None

        token_pos_to_score_pos = {}

        for i, token_pos in enumerate(replace_token_positions):
            token_pos_to_score_pos[token_pos] = i
        # 重新计算Importance score，将所有出现的位置加起来（而不是取平均）.
        names_to_importance_score = {}

        for name in names_positions_dict.keys():
            total_score = 0.0
            positions = names_positions_dict[name]
            for token_pos in positions:
                # 这个token在code中对应的位置
                # importance_score中的位置：token_pos_to_score_pos[token_pos]
                total_score += importance_score[token_pos_to_score_pos[token_pos]]

            names_to_importance_score[name] = total_score

        sorted_list_of_names = sorted(names_to_importance_score.items(), key=lambda x: x[1], reverse=True)
        # 根据importance_score进行排序

        final_words = copy.deepcopy(words)
        final_code = copy.deepcopy(code)
        nb_changed_var = 0  # 表示被修改的variable数量
        nb_changed_pos = 0
        is_success = -1
        replaced_words = {}
        for name_and_score in sorted_list_of_names:
            tgt_word = name_and_score[0]
            tgt_positions = names_positions_dict[tgt_word]

            all_substitues = []
            num = 0
            while num < 15:
                tmp_var = random.choice(self.idx2token)
                if isUID(tmp_var):
                    all_substitues.append(tmp_var)
                    num += 1

            # 得到了所有位置的substitue，并使用set来去重

            most_gap = 0.0
            candidate = None
            replace_examples = []

            substitute_list = []
            pred_list = []
            # 依次记录了被加进来的substitue
            # 即，每个temp_replace对应的substitue.

            for substitute in all_substitues:
                # temp_replace = copy.deepcopy(final_words)
                # for one_pos in tgt_positions:
                #     temp_replace[one_pos] = substitute

                substitute_list.append(substitute)
                # 记录了替换的顺序

                # 需要将几个位置都替换成sustitue_
                temp_code = get_example(final_code, tgt_word, substitute, "java")

                new_example = get_new_example(idx, temp_code, nl)
                pred = self.eval_bleu(new_example[0])
                pred_list.append(pred)
            for index, pred in enumerate(pred_list):
                # print("adv_bleu: {}, original_bleu: {}".format(pred[0], original_bleu))
                adv_code = get_example(final_code, tgt_word, candidate, "java")
                if pred[0] == 0.0:
                    is_success = 1
                    nb_changed_var += 1
                    nb_changed_pos += len(names_positions_dict[tgt_word])
                    candidate = substitute_list[index]
                    replaced_words[tgt_word] = candidate
                    print("%s SUC! %s => %s (%.5f => %.5f)" % \
                          ('>>', tgt_word, candidate,
                           current_prob, pred[0]), flush=True)
                    return is_success, adv_code, pred[1], nb_changed_var, nb_changed_pos, replaced_words
                else:
                    # 如果没有攻击成功，我们看probability的修改
                    gap = current_prob - pred[0]
                    # 并选择那个最大的gap.
                    if gap > most_gap:
                        most_gap = gap
                        candidate = substitute_list[index]

            if most_gap > 0:

                nb_changed_var += 1
                nb_changed_pos += len(names_positions_dict[tgt_word])
                current_prob = current_prob - most_gap
                replaced_words[tgt_word] = candidate
                final_code = get_example(final_code, tgt_word, candidate, "java")
                print("%s ACC! %s => %s (%.5f => %.5f)" % \
                      ('>>', tgt_word, candidate,
                       current_prob + most_gap,
                       current_prob), flush=True)
            else:
                replaced_words[tgt_word] = tgt_word

            adv_code = final_code

        return is_success, adv_code, pred[1], nb_changed_var, nb_changed_pos, replaced_words