import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt
import time
import torchvision.utils as vutils


from fleak.data.image_dataset import DatasetSplit
from fleak.model.gan_network import MnistGenerator, MnistDiscriminator, Generator, Discriminator
from fleak.utils.train_eval import train, evaluate

# Constants
Round = 300
Clinets_per_round = 10
Batch_size = 2048
Gan_epoch = 1
Test_accuracy = []
Models = {}
Model_Optimizers = {}
Client_data = {}
dataloaders = {}
# Client_labels = {}

BATCH_SIZE = 256
noise_dim = 100
num_examples_to_generate = 36
num_to_merge = 500
# num_to_merge = 50
seed = tf.random.normal([num_examples_to_generate, noise_dim])
seed_merge = tf.random.normal([num_to_merge, noise_dim])

#########################################################################
##                             Load Data                               ##
#########################################################################

# Data
# (train_images, train_labels), (test_images, test_labels) = tf.keras.datasets.mnist.load_data()
# train_images = train_images.reshape(train_images.shape[0], 28, 28, 1).astype('float32')
# train_images = (train_images - 127.5) / 127.5  # Normalization
# test_images = test_images.reshape(test_images.shape[0], 28, 28, 1).astype('float32')
# test_images = (test_images - 127.5) / 127.5  # Normalization
#
# state = np.random.get_state()
# np.random.shuffle(train_images)
# np.random.set_state(state)
# np.random.shuffle(train_labels)

device = 'cuda:0'

transform = transforms.Compose([
        # transforms.Resize(64),
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,))])
train_dataset = datasets.MNIST('../federated_learning/data/mnist', train=True, download=True, transform=transform)
test_dataset = datasets.MNIST('../federated_learning/data/mnist', train=False, transform=transform)

# Sample to warm up
warmup_dataloader = DataLoader(DatasetSplit(train_dataset, range(3000)), batch_size=256, shuffle=True)

# Each Client owns different data, Attacker has no targeted samples
for i in range(Clinets_per_round):

    # Each Client has one class
    Client_data.update({i: torch.where(train_dataset.targets == i)[0]})
    dataloaders.update({i: DataLoader(DatasetSplit(train_dataset, Client_data[i]), batch_size=Batch_size, shuffle=True)})
    # Client_labels.update({i: train_labels[train_labels == i]})
    # # Shuffle
    # state = np.random.get_state()
    # np.random.shuffle(Client_data[i])
    # np.random.set_state(state)
    # np.random.shuffle(Client_labels[i])
    # print(len(train_labels[train_labels==i]))

# attack_ds = np.array(Client_data[0])
# attack_l = np.array(Client_labels[0])


#########################################################################
##                          Models Prepared                            ##
#########################################################################

# Models & malicious discriminator model
# def make_discriminator_model():
#     model = keras.Sequential()
#     model.add(keras.layers.Conv2D(64, (5, 5), strides=(2, 2), padding='same', input_shape=[28, 28, 1]))
#     model.add(keras.layers.LeakyReLU())
#     model.add(keras.layers.Dropout(0.3))
#
#     model.add(keras.layers.Conv2D(128, (5, 5), strides=(2, 2), padding='same'))
#     model.add(keras.layers.LeakyReLU())
#     model.add(keras.layers.Dropout(0.3))
#
#     model.add(keras.layers.Flatten())
#     model.add(keras.layers.Dense(11))
#     return model


# Malicious generator model
# def make_generator_model():
#     model = keras.Sequential()
#
#     model.add(keras.layers.Dense(7 * 7 * 256, use_bias=False, input_shape=(100,)))
#     model.add(keras.layers.BatchNormalization())
#     model.add(keras.layers.ReLU())
#
#     model.add(keras.layers.Reshape((7, 7, 256)))
#     assert model.output_shape == (None, 7, 7, 256)  # Batch size is not limited
#
#     model.add(keras.layers.Conv2DTranspose(128, (4, 4), strides=(1, 1), padding='same', use_bias=False))
#     assert model.output_shape == (None, 7, 7, 128)
#     model.add(keras.layers.BatchNormalization())
#     model.add(keras.layers.ReLU())
#
#     model.add(keras.layers.Conv2DTranspose(64, (4, 4), strides=(2, 2), padding='same', use_bias=False))
#     assert model.output_shape == (None, 14, 14, 64)
#     model.add(keras.layers.BatchNormalization())
#     model.add(keras.layers.ReLU())
#
#     model.add(
#         keras.layers.Conv2DTranspose(1, (4, 4), strides=(2, 2), padding='same', use_bias=False, activation='tanh'))
#     assert model.output_shape == (None, 28, 28, 1)
#
#     return model


# Model
# Sever‘s models
model = MnistDiscriminator()
warmup_optimizer = optim.Adam(model.parameters(), lr=1e-3)
criterion = nn.CrossEntropyLoss()

# Clients' models
for i in range(Clinets_per_round):
    Models.update({i: MnistDiscriminator()})
    Model_Optimizers.update({i: optim.Adam(Models[i].parameters(), lr=1e-3)})
        # compile(optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        #               loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        #               metrics=['accuracy'])

#########################################################################
##                            Attack setup                             ##
#########################################################################

# Malicious gan
generator = MnistGenerator()
malicious_discriminator = MnistDiscriminator()

# Cross entropy
# cross_entropy = keras.losses.SparseCategoricalCrossentropy(from_logits=True)
cross_entropy = nn.CrossEntropyLoss()


# Loss of discriminator
# def discriminator_loss(real_output, fake_output, real_labels):
#     # real_loss = cross_entropy(real_labels, real_output)
#     real_loss = cross_entropy(real_output, real_labels)
#
#     # fake_result = np.zeros(len(fake_output))
#     # # Attack label
#     # for i in range(len(fake_result)):
#     #     fake_result[i] = 10
#     fake_result = torch.full(real_labels.shape, )
#
#     fake_loss = cross_entropy(fake_result, fake_output)
#     total_loss = real_loss + fake_loss
#     return total_loss
#
#
# # Loss of generator
# def generator_loss(fake_output):
#     ideal_result = np.zeros(len(fake_output))
#     # Attack label
#     for i in range(len(ideal_result)):
#         # The class which attacker intends to get
#         ideal_result[i] = 3
#
#     return cross_entropy(ideal_result, fake_output)


# Optimizer
# generator_optimizer = optim.SGD(learning_rate=1e-3, decay=1e-7)
generator_optimizer = optim.SGD(generator.parameters(), lr=1e-3, weight_decay=1e-7)
# discriminator_optimizer = tf.keras.optimizers.SGD(learning_rate=1e-4, decay=1e-7)
discriminator_optimizer = optim.SGD(malicious_discriminator.parameters(), lr=1e-4, weight_decay=1e-7)

# Training step
# @tf.function
# def train_step(images, labels):
#     noise = tf.random.normal([BATCH_SIZE, noise_dim])
#
#     with tf.GradientTape() as gen_tape, tf.GradientTape() as disc_tape:
#         generated_images = generator(noise, training=True)
#
#         # real_output is the probability of the mimic number
#         real_output = malicious_discriminator(images, training=False)
#         fake_output = malicious_discriminator(generated_images, training=False)
#
#         gen_loss = generator_loss(fake_output)
#         disc_loss = discriminator_loss(real_output, fake_output, real_labels=labels)
#
#     gradients_of_generator = gen_tape.gradient(gen_loss, generator.trainable_variables)
#     gradients_of_discriminator = disc_tape.gradient(disc_loss, malicious_discriminator.trainable_variables)
#
#     generator_optimizer.apply_gradients(zip(gradients_of_generator, generator.trainable_variables))
#     discriminator_optimizer.apply_gradients(
#         zip(gradients_of_discriminator, malicious_discriminator.trainable_variables))


# Train
def train_gan(dataloader, epochs):
    for epoch in range(epochs):
        start = time.time()
        for i, (features, labels) in enumerate(dataloader):
            features, labels = features.to(device), labels.to(device)
            noise = torch.randn(Batch_size, noise_dim, device=device)

            # train generator
            generator.train()
            malicious_discriminator.eval()
            generator_optimizer.zero_grad()

            generated_images = generator(noise)
            fake_output = malicious_discriminator(generated_images)
            tracked_labels = torch.full(labels.shape, 3, device=device)

            g_loss = cross_entropy(fake_output, tracked_labels)
            g_loss.backward()
            generator_optimizer.step()

            # train discriminator
            generator.eval()
            malicious_discriminator.train()
            discriminator_optimizer.zero_grad()

            real_output = malicious_discriminator(features)


        for i in range(round(len(dataset) / BATCH_SIZE)):
            image_batch = dataset[i * BATCH_SIZE:min(len(dataset), (i + 1) * BATCH_SIZE)]
            labels_batch = labels[i * BATCH_SIZE:min(len(dataset), (i + 1) * BATCH_SIZE)]
            train_step(image_batch, labels_batch)

        print('Time for epoch {} is {} sec'.format(epoch + 1, time.time() - start))

    # Last epoch generate the images and merge them to the dataset
    generate_and_save_images(generator, epochs, seed)


# Generate images to check the effect
def generate_and_save_images(model, epoch, test_input):
    predictions = model(test_input, training=False)

    fig = plt.figure(figsize=(6, 6))

    for i in range(predictions.shape[0]):
        plt.subplot(6, 6, i + 1)
        plt.imshow(predictions[i, :, :, 0] * 127.5 + 127.5, cmap='gray')
        plt.axis('off')

    plt.savefig('image_at_epoch_{:04d}.png'.format(epoch))


#########################################################################
##                         Federated Learning                          ##
#########################################################################

# Training Preparation
# model.compile(optimizer=keras.optimizers.Adam(learning_rate=1e-3),
#               loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
#               metrics=['accuracy'])
#
# model.fit(warm_up_data, warm_up_labels, validation_split=0, epochs=25, batch_size=256)
# del train_images, train_labels

for _ in range(25):
    train(model, device, warmup_dataloader, warmup_optimizer, criterion)

tmp_weight = model.state_dict()

attack_count = 0

# Federated learning
for r in range(Round):
    print('round:' + str(r + 1))
    model_weights_sum = []
    # model_weight_tmp = []
    # tmp_weight = model.get_weights()

    for i in range(Clinets_per_round):

        # train the clients individually
        # if r != 0:
        #     Models[i].set_weights(tmp_weight)
        Models[i].load_state_dict(tmp_weight)

        # train_ds = Client_data[i]
        # train_l = Client_labels[i]
        train_ds = dataloaders[i]

        # Attack (suppose client 0 is malicious)
        if r != 0 and i == 0 and Test_accuracy[i - 1] > 0.85:
            print("Attack round: {}".format(attack_count + 1))

            malicious_discriminator.load_state_dict(Models[i].state_dict())
            # train(attack_ds, attack_l, Gan_epoch)
            train(attack_ds, attack_l, Gan_epoch)

            predictions = generator(seed_merge, training=False)
            malicious_images = np.array(predictions)
            malicious_labels = np.array([1] * len(malicious_images))

            # Merge the malicious images
            if attack_count == 0:
                Client_data[i] = np.vstack((Client_data[i], malicious_images))
                # Label the malicious images
                Client_labels[i] = np.append(Client_labels[i], malicious_labels)
            else:
                Client_data[i][len(Client_data[i]) - len(malicious_images):len(Client_data[i])] = malicious_images

            attack_count += 1

        Models[i].fit(train_ds, train_l, validation_split=0, epochs=1, batch_size=Batch_size)

        if i == 0:
            model_weights_sum = np.array(Models[i].get_weights())
            # model_weight_tmp = np.array(Models[i].get_weights())
        else:
            model_weights_sum += np.array(Models[i].get_weights())
            # delta_weight = np.array(Models[i].get_weights()) - np.array(tmp_weight)
            # model_weight_tmp += delta_weight

    # averaging the weights
    mean_weight = np.true_divide(model_weights_sum, Clinets_per_round)
    tmp_weight = mean_weight.tolist()
    del model_weights_sum
    # tmp_weight = model_weight_tmp
    # del model_weight_tmp

    # evaluate
    model.set_weights(tmp_weight)
    test_loss, test_acc = model.evaluate(test_images, test_labels, verbose=0)
    Test_accuracy.append(test_acc)
    print('\nTest accuracy:', test_acc, 'Tset loss:', test_loss)