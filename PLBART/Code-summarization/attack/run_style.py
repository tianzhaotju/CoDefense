import os

os.system("python attack_style.py \
    --output_dir=../saved_models \
    --model_name_or_path ../../../Model/PLBART/checkpoint_11_100000.pt \
    --dev_filename=../../../Data/Code-summarization/test_sampled.jsonl \
    --load_model_path ../saved_models/checkpoint-best-bleu/pytorch_model.bin \
    --csv_store_path1 ../result/plbart_sum_style.csv \
    --tokenizer_name=../../../Model/PLBART/sentencepiece.bpe.model \
    --max_source_length 256 \
    --max_target_length 128 \
    --beam_size 10 \
    --eval_batch_size 64 \
    --seed 123456  2>&1")

