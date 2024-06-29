import os

os.system("python attack_alert.py \
    --output_dir=../saved_models \
    --model_name_or_path=../../checkpoint_11_100000.pt \
    --tokenizer_name=../../sentencepiece.bpe.model \
    --base_model=microsoft/codebert-base-mlm \
    --csv_store_path ../result/plbart_clone_alert.csv \
    --use_ga \
    --eval_data_file=../../../Data/Clone-detection/test_sampled.txt \
    --block_size 512 \
    --eval_batch_size 64 \
    --seed 123456")

