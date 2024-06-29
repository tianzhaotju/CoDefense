import os

os.system("python run.py \
    --output_dir=../saved_models_codebert_clone_style/ \
    --model_type=roberta \
    --config_name=microsoft/codebert-base \
    --model_name_or_path=microsoft/codebert-base \
    --tokenizer_name=roberta-base \
    --do_test \
    --train_data_file=../../../adv_data/Clone-detection/CodeBERT/alert/adv_train.txt \
    --eval_data_file=../../../adv_data/Clone-detection/CodeBERT/alert/valid.txt \
    --test_data_file=../../../adv_data/Clone-detection/CodeBERT/alert/adv_test_2.txt \
    --epoch 2 \
    --block_size 400 \
    --train_batch_size 16 \
    --eval_batch_size 32 \
    --learning_rate 5e-5 \
    --max_grad_norm 1.0 \
    --evaluate_during_training \
    --seed 123456 2>&1")

