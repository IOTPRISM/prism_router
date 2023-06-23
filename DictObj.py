class DictObj():
    
    def __init__(self, dictionary=None) -> None:
        if dictionary:
            for key, val in dict(dictionary).items():
                setattr(self, key, val)
    
    def __getitem__(self, key):
        return getattr(self, key)
    
    def __setitem__(self, key, val) -> None:
        setattr(self, key, val)

    def __str__(self) -> str:
        return str(vars(self))