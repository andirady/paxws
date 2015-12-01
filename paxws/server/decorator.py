def service(tns=None, location=None):
    def f(kls):
        kls._target_namespace = tns
        kls._endpoint = location
        return kls
    return f
