import os
os.system("python run.py \
    --output_dir=../saved_models_codebert_sum_alert/ \
    --do_train \
    --do_eval \
    --model_type roberta \
    --model_name_or_path microsoft/codebert-base \
    --train_filename=../../../adv_data/Code-summarization/CodeBERT/alert/adv_train.jsonl \
    --dev_filename=../../../adv_data/Code-summarization/CodeBERT/alert/valid.jsonl \
    --test_filename=../../../adv_data/Code-summarization/CodeBERT/alert/adv_test_2.jsonl \
    --max_source_length 256 \
    --max_target_length 128 \
    --beam_size 10 \
    --train_batch_size 8 \
    --eval_batch_size 8 \
    --learning_rate 5e-5 \
    --num_train_epochs 10 \
    2>&1")

