from __future__ import absolute_import
from deepchem.nn.keras import backend as K
from deepchem.nn.keras.utils.generic_utils import get_from_module


class Regularizer(object):

  def set_param(self, p):
    self.p = p

  def set_layer(self, layer):
    self.layer = layer

  def __call__(self, loss):
    return loss

  def get_config(self):
    return {'name': self.__class__.__name__}


class EigenvalueRegularizer(Regularizer):
  '''This takes a constant that controls
  the regularization by Eigenvalue Decay on the
  current layer and outputs the regularized
  loss (evaluated on the training data) and
  the original loss (evaluated on the
  validation data).
  '''
  def __init__(self, k):
    self.k = k
    self.uses_learning_phase = True

  def set_param(self, p):
    if hasattr(self, 'p'):
      raise Exception('Regularizers cannot be reused. '
                      'Instantiate one regularizer per layer.')
    self.p = p

  def __call__(self, loss):
    power = 9  # number of iterations of the power method
    W = self.p
    if K.ndim(W) > 2:
      raise Exception('Eigenvalue Decay regularizer '
                      'is only available for dense '
                      'and embedding layers.')
    WW = K.dot(K.transpose(W), W)
    dim1, dim2 = K.eval(K.shape(WW))  # number of neurons in the layer

    # power method for approximating the dominant eigenvector:
    o = K.ones([dim1, 1])  # initial values for the dominant eigenvector
    main_eigenvect = K.dot(WW, o)
    for n in range(power - 1):
      main_eigenvect = K.dot(WW, main_eigenvect)

    WWd = K.dot(WW, main_eigenvect)

    # the corresponding dominant eigenvalue:
    main_eigenval = (K.dot(K.transpose(WWd), main_eigenvect) /
                     K.dot(K.transpose(main_eigenvect), main_eigenvect))
    # multiplied by the given regularization gain
    regularized_loss = loss + (main_eigenval ** 0.5) * self.k

    return K.in_train_phase(regularized_loss[0, 0], loss)


class WeightRegularizer(Regularizer):

  def __init__(self, l1=0., l2=0.):
    self.l1 = K.cast_to_floatx(l1)
    self.l2 = K.cast_to_floatx(l2)
    self.uses_learning_phase = True
    self.p = None

  def set_param(self, p):
    if self.p is not None:
      raise Exception('Regularizers cannot be reused. '
                      'Instantiate one regularizer per layer.')
    self.p = p

  def __call__(self, loss):
    if self.p is None:
      raise Exception('Need to call `set_param` on '
                      'WeightRegularizer instance '
                      'before calling the instance. '
                      'Check that you are not passing '
                      'a WeightRegularizer instead of an '
                      'ActivityRegularizer '
                      '(i.e. activity_regularizer="l2" instead '
                      'of activity_regularizer="activity_l2".')
    regularized_loss = loss
    if self.l1:
      regularized_loss += K.sum(self.l1 * K.abs(self.p))
    if self.l2:
      regularized_loss += K.sum(self.l2 * K.square(self.p))
    return K.in_train_phase(regularized_loss, loss)

  def get_config(self):
    return {'name': self.__class__.__name__,
            'l1': float(self.l1),
            'l2': float(self.l2)}


class ActivityRegularizer(Regularizer):

  def __init__(self, l1=0., l2=0.):
    self.l1 = K.cast_to_floatx(l1)
    self.l2 = K.cast_to_floatx(l2)
    self.uses_learning_phase = True
    self.layer = None

  def set_layer(self, layer):
    if self.layer is not None:
      raise Exception('Regularizers cannot be reused')
    self.layer = layer

  def __call__(self, loss):
    if self.layer is None:
      raise Exception('Need to call `set_layer` on '
                      'ActivityRegularizer instance '
                      'before calling the instance.')
    regularized_loss = loss
    for i in range(len(self.layer.inbound_nodes)):
      output = self.layer.get_output_at(i)
      if self.l1:
        regularized_loss += K.sum(self.l1 * K.abs(output))
      if self.l2:
        regularized_loss += K.sum(self.l2 * K.square(output))
    return K.in_train_phase(regularized_loss, loss)

  def get_config(self):
    return {'name': self.__class__.__name__,
            'l1': float(self.l1),
            'l2': float(self.l2)}


def l1(l=0.01):
  return WeightRegularizer(l1=l)


def l2(l=0.01):
  return WeightRegularizer(l2=l)


def l1l2(l1=0.01, l2=0.01):
  return WeightRegularizer(l1=l1, l2=l2)


def activity_l1(l=0.01):
  return ActivityRegularizer(l1=l)


def activity_l2(l=0.01):
  return ActivityRegularizer(l2=l)


def activity_l1l2(l1=0.01, l2=0.01):
  return ActivityRegularizer(l1=l1, l2=l2)


def get(identifier, kwargs=None):
  return get_from_module(identifier, globals(), 'regularizer',
                         instantiate=True, kwargs=kwargs)