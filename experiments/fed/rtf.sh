BASE_DATADIR="../federated_learning/data"

cd ..
cd ..

# run robbing the fed
# non-iid
python server_attack.py \
    --attack rtf \
    --model resnet18 \
    --imprint \
    --base_data_dir $BASE_DATADIR \
    --dataset cifar10 \
    --normalize \
    --p_type dirichlet \
    --beta 0.5 \
    --total_clients 100 \
    --num_rounds 1 \
    --local_epochs 1 \
    --batch_size 10 \
    --lr 0.1 \
    --lr_decay 0.95 \
    --client_momentum 0 \
    --device cuda \
    --save_results

# run robbing the fed
# iid
python server_attack.py \
    --attack rtf \
    --model resnet18 \
    --imprint \
    --base_data_dir $BASE_DATADIR \
    --dataset cifar10 \
    --normalize \
    --iid \
    --total_clients 100 \
    --num_rounds 1 \
    --local_epochs 1 \
    --batch_size 10 \
    --lr 0.1 \
    --lr_decay 0.95 \
    --client_momentum 0 \
    --device cuda \
    --save_results