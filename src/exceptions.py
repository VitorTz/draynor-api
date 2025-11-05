

class DatabaseError(Exception):
    
    def __init__(self, detail: str, code: str = None):
        super().__init__(detail)
        self.detail = detail
        self.code = code

    def __str__(self):
        base = f"[DatabaseError] {self.detail}"
        if self.code: base += f" (code: {self.code})"
        return base
