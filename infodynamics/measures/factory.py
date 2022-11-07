"""Factory function for Entropies classes."""

from infodynamics.entropies.entropy_measures import kld, jsd, cosine_distance


def metric_factory(metric_name):
    mapping = {
        'kld': kld,
        'jsd': jsd,
        'cosince': cosine_distance
    }

    return mapping[metric_name]

# def metric_factory(model, *args, **kwargs):
#     for cls in BaseMetric.__subclasses__():
#         if cls.model == model:
#             return cls(*args, **kwargs)
#     raise ValueError("Not such model: {}".format(model))