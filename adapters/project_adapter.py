from ncs_method.core import MethodError

def keyed_reorder(actual, expected, label):
    actual=list(actual);expected=list(expected)
    if len(actual)!=len(set(actual)) or set(actual)!=set(expected):raise MethodError(label+': keys differ or duplicate')
    lookup={k:i for i,k in enumerate(actual)}
    return [lookup[k] for k in expected]
