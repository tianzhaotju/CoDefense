import os

os.system("python attack_style.py \
    --output_dir=../saved_models \
    --model_type=roberta \
    --tokenizer_name=microsoft/codebert-base \
    --model_name_or_path=microsoft/codebert-base \
    --base_model=microsoft/codebert-base-mlm \
    --csv_store_path1 ../result/codebert_clone_style.csv \
    --eval_data_file=../../../Data/Clone-detection/test_sampled.txt \
    --block_size 512 \
    --eval_batch_size 32 \
    --seed 123456  2>&1")

