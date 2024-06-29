import os

os.system("python run.py \
    --output_dir=../saved_models_plbart_clone_style/ \
    --model_type=bart \
    --model_name_or_path=../../checkpoint_11_100000.pt \
    --tokenizer_name=../../sentencepiece.bpe.model \
    --do_train \
    --train_data_file=../../../adv_data/Clone-detection/PLBART/style/adv_train.txt \
    --eval_data_file=../../../adv_data/Clone-detection/PLBART/style/valid.txt \
    --test_data_file=../../../adv_data/Clone-detection/PLBART/style/test_2.txt \
    --epoch 2 \
    --block_size 400 \
    --train_batch_size 16 \
    --eval_batch_size 32 \
    --learning_rate 5e-5 \
    --max_grad_norm 1.0 \
    --evaluate_during_training \
    --seed 123456 2>&1")

