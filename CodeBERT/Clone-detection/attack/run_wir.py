import os

os.system("python attack_wir.py \
    --output_dir=../saved_models \
    --model_type=roberta \
    --tokenizer_name=microsoft/codebert-base \
    --model_name_or_path=microsoft/codebert-base \
    --csv_store_path ../result/codebert_clone_wir.csv \
    --base_model=microsoft/codebert-base-mlm \
    --eval_data_file=../../../Data/Clone-detection/test_sampled.txt \
    --block_size 512 \
    --eval_batch_size 32 \
    --seed 123456")

