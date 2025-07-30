# Puppet AI

Puppet, yapay zeka modelleri oluşturmak, eğitmek ve yönetmek için tasarlanmış bir Python modülüdür. Kullanımı kolay bir arayüz sunarak makine öğrenimi modellerinin geliştirilmesini ve dağıtılmasını kolaylaştırır.

## Özellikler

- Kolay model oluşturma ve yönetme
- Eğitim ve değerlendirme için kullanıcı dostu API'ler
- Model serileştirme ve yükleme desteği
- Genişletilebilir mimari

## Kurulum

```bash
pip install -e .
```

## Hızlı Başlangıç

```python
from puppet import PuppetModel

# Özel model sınıfınızı oluşturun
class MyModel(PuppetModel):
    def train(self, data, **kwargs):
        # Eğitim mantığınızı buraya ekleyin
        self.is_trained = True
        return {"accuracy": 0.95}
    
    def predict(self, input_data):
        # Tahmin mantığınızı buraya ekleyin
        return [0] * len(input_data)

# Modeli oluştur ve kullan
model = MyModel("my_awesome_model")
model.train(training_data)
predictions = model.predict(test_data)
```

## Geliştirme

Geliştirme yapmak için gerekli bağımlılıkları yükleyin:

```bash
pip install -e ".[dev]"
```

Testleri çalıştırmak için:

```bash
pytest
```

## Lisans

MIT
