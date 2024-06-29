import sys
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

sys.path.append('../code')
sys.path.append('../../../')
sys.path.append('../../../python_parser')

import json
import logging
import argparse
import warnings
import torch
import time
from tqdm import tqdm
from run import InputFeatures, convert_examples_to_features
from model import Model
from run import TextDataset
from utils import CodeDataset
from utils import set_seed
from utils import Recorder_style
from attacker import Style_Attacker, get_code_pairs, get_transfered_code
from transformers import (RobertaForMaskedLM, RobertaConfig, RobertaModel, RobertaTokenizer)

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.simplefilter(action='ignore', category=FutureWarning)  # Only report warning

MODEL_CLASSES = {
    'roberta': (RobertaConfig, RobertaModel, RobertaTokenizer)
}

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()

    ## Required parameters
    parser.add_argument("--output_dir", default=None, type=str, required=True,
                        help="The output directory where the model predictions and checkpoints will be written.")

    ## Other parameters
    parser.add_argument("--block_size", default=-1, type=int,
                        help="Optional input sequence length after tokenization."
                             "The training dataset will be truncated in block of this size for training."
                             "Default to the model max input length for single sentence inputs (take into account special tokens).")
    parser.add_argument("--eval_data_file", default=None, type=str,
                        help="An optional input evaluation data file to evaluate the perplexity on (a text file).")
    parser.add_argument("--model_type", default="bert", type=str,
                        help="The model architecture to be fine-tuned.")
    parser.add_argument("--model_name_or_path", default=None, type=str,
                        help="The model checkpoint for weights initialization.")
    parser.add_argument("--base_model", default=None, type=str,
                        help="Base Model")
    parser.add_argument("--csv_store_path1", default=None, type=str,
                        help="Base Model")
    parser.add_argument("--config_name", default="", type=str,
                        help="Optional pretrained config name or path if not the same as model_name_or_path")
    parser.add_argument("--tokenizer_name", default="", type=str,
                        help="Optional pretrained tokenizer name or path if not the same as model_name_or_path")
    parser.add_argument("--data_flow_length", default=64, type=int,
                        help="Optional Data Flow input sequence length after tokenization.")
    parser.add_argument("--code_length", default=256, type=int,
                        help="Optional Code input sequence length after tokenization.")
    parser.add_argument("--do_train", action='store_true',
                        help="Whether to run training.")
    parser.add_argument("--use_ga", action='store_true',
                        help="Whether to GA-Attack.")
    parser.add_argument("--eval_batch_size", default=4, type=int,
                        help="Batch size per GPU/CPU for evaluation.")
    parser.add_argument('--seed', type=int, default=42,
                        help="random seed for initialization")
    parser.add_argument("--cache_dir", default="", type=str,
                        help="Optional directory to store the pre-trained models downloaded from s3 (instread of the default one)")

    args = parser.parse_args()
    args.device = torch.device("cuda")
    # Set seed
    set_seed(args.seed)
    print("start")
    config_class, model_class, tokenizer_class = MODEL_CLASSES[args.model_type]
    config = config_class.from_pretrained(args.config_name if args.config_name else args.model_name_or_path,
                                          cache_dir=args.cache_dir if args.cache_dir else None)
    config.num_labels = 2
    tokenizer = tokenizer_class.from_pretrained(args.tokenizer_name,
                                                do_lower_case=False,
                                                cache_dir=args.cache_dir if args.cache_dir else None)
    args.block_size = min(args.block_size, tokenizer.max_len_single_sentence)
    if args.model_name_or_path:
        model = model_class.from_pretrained(args.model_name_or_path,
                                            from_tf=bool('.ckpt' in args.model_name_or_path),
                                            config=config,
                                            cache_dir=args.cache_dir if args.cache_dir else None)
    else:
        model = model_class(config)

    model = Model(model, config, tokenizer, args)
    checkpoint_prefix = 'checkpoint-best-f1/model.bin'
    output_dir = os.path.join(args.output_dir, '{}'.format(checkpoint_prefix))
    model.load_state_dict(torch.load(output_dir))
    model.to(args.device)
    logger.info("reload model from {}".format(output_dir))

    tokenizer_mlm = RobertaTokenizer.from_pretrained(args.base_model)
    # Load Dataset
    eval_dataset = TextDataset(tokenizer, args, args.eval_data_file)
    ## Load code pairs
    source_codes = get_code_pairs(args.eval_data_file, tokenizer, args)
    subs_path = "../../../dataset/preprocess/test_subs_clone.jsonl"
    labels, code1_list = [], []
    with open(subs_path) as f:
        for line in f:
            js = json.loads(line.strip())
            code1_list.append(js['code1'])
            labels.append(js["label"])

    recoder1 = Recorder_style(args.csv_store_path1)
    attacker = Style_Attacker(args, model, tokenizer, tokenizer_mlm)
    print("ATTACKER BUILT!")
    success_attack, total_cnt, index_start, index_end = 0, 0, 0, 4000
    start_time = time.time()
    print("index_start:", index_start)
    print("index_end:", index_end)
    for index, example in tqdm(enumerate(eval_dataset), total=index_end-index_start):
        if index < index_start:
            continue
        if index >= index_end:
            break
        code_pair = source_codes[index]
        _, orig_label = model.get_results([example], args.eval_batch_size)
        true_label = example[1].item()
        orig_label = orig_label[0]
        if not orig_label == true_label:
            continue
        first_code = code_pair[2].strip()
        total_adv_codes = {' '.join(first_code.split()).strip(): true_label}
        adv_codes = get_transfered_code(first_code)
        if len(adv_codes) == 0:
            recoder1.write(index, first_code, first_code, true_label, orig_label, true_label,
                           round((time.time() - start_time) / 60, 2))
            continue
        query_times, is_success, adv_codes_attack = 0, -1, []
        code_2 = " ".join(code_pair[3].split())
        words_2 = tokenizer.tokenize(code_2)
        example_start_time = time.time()
        total_cnt += 1
        print("attack(1)_len(adv_codes)", len(adv_codes))
        for adv_code in adv_codes:
            tmp_code = ' '.join(adv_code.split())
            if tmp_code.strip() in total_adv_codes.keys():
                pred_label = total_adv_codes[tmp_code.strip()]
            else:
                tmp_code_ = tokenizer.tokenize(tmp_code)
                tmp_feature = convert_examples_to_features(tmp_code_, words_2, true_label, None, None, tokenizer, args, None)
                new_dataset = CodeDataset([tmp_feature])
                logits, preds = model.get_results(new_dataset, args.eval_batch_size)
                pred_label = preds[0]
                total_adv_codes[tmp_code.strip()] = pred_label
            query_times += 1
            example_end_time = (time.time() - example_start_time) / 60
            if pred_label != true_label:
                is_success = 1
                print("%s SUC! (%.5f => %.5f)" % ('>>', true_label, pred_label), flush=True)
                print("Example time cost: ", round(example_end_time, 2), "min")
                print("ALL examples time cost: ", round((time.time() - start_time) / 60, 2), "min")
                print("Query times in this attack: ", query_times)
                success_attack += 1
                adv_label = "1" if true_label == 0 else "0"
                if len(adv_code) > 30000:
                    adv_code_part = adv_code[:30000]
                    recoder1.write(index, code_pair[0], adv_code_part, true_label, orig_label, adv_label,
                                  round((time.time() - start_time) / 60, 2))
                    remaining_adv_code = adv_code[30000:]
                    recoder1.write("", "", remaining_adv_code, "", "", "", "")
                else:
                    recoder1.write(index, code_pair[0], adv_code, true_label, orig_label, adv_label,
                                  round((time.time() - start_time) / 60, 2))
                print("Success rate is : {}/{} = {}".format(success_attack, total_cnt,
                                                            1.0 * success_attack / total_cnt))
                break
        for adv_code in adv_codes:
            new_adv_codes = get_transfered_code(adv_code)
            adv_codes_attack += new_adv_codes
        # fail
        if is_success == -1:
            print("Attack 1 failed on index = {}.".format(index))
            while True:
                is_success, final_code, adv_code, query_times, total_adv_codes = attacker.style_attack(code_pair, true_label, example, adv_codes_attack, query_times, total_adv_codes)
                adv_codes_attack = adv_code
                if is_success == 1 or query_times >= 15:
                    break
            example_end_time = (time.time() - example_start_time) / 60
            if is_success == 1:
                success_attack += 1
                adv_label = "1" if true_label == 0 else "0"
                if len(adv_code) > 30000:
                    adv_code_part = adv_code[:30000]
                    recoder1.write(index, first_code, adv_code_part, true_label, orig_label, adv_label,
                                  round((time.time() - start_time) / 60, 2))
                    remaining_adv_code = adv_code[30000:]
                    recoder1.write("", "", remaining_adv_code, "", "", "", "")
                else:
                    recoder1.write(index, first_code, adv_code, true_label, orig_label, adv_label,
                                  round((time.time() - start_time) / 60, 2))

                recoder1.write(index, code_pair[0], adv_code, true_label, orig_label, adv_label, round((time.time() - start_time) / 60, 2))
            else:
                adv_label = "1" if true_label == 1 else "0"
                if len(final_code) > 30000:
                    final_code_part = adv_code[:30000]
                    recoder1.write(index, first_code, final_code_part, true_label, orig_label, adv_label,
                                  round((time.time() - start_time) / 60, 2))
                    remaining_final_code = final_code[30000:]
                    recoder1.write("", "", remaining_final_code, "", "", "", "")
                else:
                    recoder1.write(index, first_code, final_code, true_label, orig_label, adv_label,
                                  round((time.time() - start_time) / 60, 2))
        print("Success rate is : {}/{} = {}".format(success_attack, total_cnt, 1.0 * success_attack / total_cnt))
        print("ALL examples time cost: ", round((time.time() - start_time) / 60, 2), "min")
        print("Query times in this attack: ", query_times)


if __name__ == '__main__':
    main()