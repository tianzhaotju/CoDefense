import os
os.system("python run.py \
    --output_dir=../saved_models_codegpt_sum_style/ \
    --model_type=gpt2 \
    --model_name_or_path=microsoft/CodeGPT-small-java-adaptedGPT2 \
    --do_train \
    --do_eval \
    --train_filename=../../../adv_data/Code-summarization/CodeGPT/style/adv_train.jsonl \
    --dev_filename=../../../adv_data/Code-summarization/CodeGPT/style/valid.jsonl \
    --test_filename=../../../adv_data/Code-summarization/CodeGPT/style/adv_test_2.jsonl \
    --max_source_length 256 \
    --max_target_length 128 \
    --beam_size 10 \
    --train_batch_size 16 \
    --eval_batch_size 16 \
    --learning_rate 5e-5 \
    --num_train_epochs 10 \
    2>&1")

