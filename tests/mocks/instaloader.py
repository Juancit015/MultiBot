"""Módulo instaloader simulado para el flujo de carruseles de Instagram."""
import types

_NODES = 4


def make_instaloader_module(typename="GraphSidecar", error=False, nodes=4):
    class FakePost:
        def __init__(self, t):
            self.typename = t
        likes = 10
        owner_username = "owner"
        caption = "cap"

        def get_sidecar_nodes(self):
            return [type("N", (), {"display_url": f"https://cdn.ig/{i}"})() for i in range(nodes)]

    mod = types.ModuleType("instaloader")

    class L:
        def __init__(self):
            self.context = object()

        def load_session_from_file(self, p):
            raise FileNotFoundError

    class P:
        @staticmethod
        def from_shortcode(ctx, sc):
            if error:
                raise RuntimeError("insta boom")
            return FakePost(typename)

    mod.Instaloader = L
    mod.Post = P
    return mod