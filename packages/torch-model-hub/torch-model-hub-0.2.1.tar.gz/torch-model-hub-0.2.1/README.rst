Usage Sample
''''''''''''

.. code:: python

        import torch
        from model.model import TextCNN
        X = torch.randn(8, 10, 128)
        model = TextCNN(embed_dim=128, kernel_sizes=(2, 3, 4), cnn_channels=64, out_features=2)
        output = model(X)
