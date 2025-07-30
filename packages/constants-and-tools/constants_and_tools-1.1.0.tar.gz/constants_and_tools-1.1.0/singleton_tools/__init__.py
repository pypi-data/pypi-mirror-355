class SingletonMeta(type):
    """
    Metaclase para que la clase que la herede sea instanciada solo una vez y referenciada en las siguientes
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]