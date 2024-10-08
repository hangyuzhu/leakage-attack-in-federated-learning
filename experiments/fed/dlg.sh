BASE_DATADIR="../federated_learning/data"

cd ..
cd ..

# run dlg
# non-iid
python server_attack.py \
    --attack dlg \
    --model cnn \
    --base_data_dir $BASE_DATADIR \
    --dataset cifar10 \
    --normalize \
    --p_type dirichlet \
    --beta 0.5 \
    --total_clients 100 \
    --num_rounds 2 \
    --local_epochs 1 \
    --batch_size 10 \
    --lr 0.1 \
    --lr_decay 0.95 \
    --client_momentum 0 \
    --rec_epochs 300 \
    --rec_batch_size 10 \
    --rec_lr 1.0 \
    --device cuda \
    --save_results

# run idlg
# non-iid
python server_attack.py \
    --attack idlg \
    --model cnn \
    --base_data_dir $BASE_DATADIR \
    --dataset cifar10 \
    --normalize \
    --p_type dirichlet \
    --beta 0.5 \
    --total_clients 100 \
    --num_rounds 20 \
    --local_epochs 1 \
    --batch_size 10 \
    --lr 0.1 \
    --lr_decay 0.95 \
    --client_momentum 0 \
    --rec_epochs 300 \
    --rec_batch_size 1 \
    --rec_lr 1.0 \
    --device cuda \
    --save_results