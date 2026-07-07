class AutomationContext:
    """Explicit runtime surface used by automation tasks."""

    def __init__(self, runtime):
        self.runtime = runtime

    @property
    def config(self):
        return self.runtime.config

    @property
    def regions(self):
        return self.runtime.regions

    @property
    def is_running(self):
        return self.runtime.is_running

    @property
    def is_paused(self):
        return getattr(self.runtime, "is_paused", False)

    @property
    def detail_state_confirmed(self):
        return getattr(self.runtime, "detail_state_confirmed", False)

    @detail_state_confirmed.setter
    def detail_state_confirmed(self, value):
        self.runtime.detail_state_confirmed = value

    @property
    def race_counter(self):
        return self.runtime.race_counter

    @race_counter.setter
    def race_counter(self, value):
        self.runtime.race_counter = value

    @property
    def car_counter(self):
        return self.runtime.car_counter

    @car_counter.setter
    def car_counter(self, value):
        self.runtime.car_counter = value

    @property
    def cj_counter(self):
        return self.runtime.cj_counter

    @cj_counter.setter
    def cj_counter(self, value):
        self.runtime.cj_counter = value

    @property
    def sc_count(self):
        return self.runtime.sc_count

    @sc_count.setter
    def sc_count(self, value):
        self.runtime.sc_count = value

    @property
    def memory_car_page(self):
        return getattr(self.runtime, "memory_car_page", 0)

    @memory_car_page.setter
    def memory_car_page(self, value):
        self.runtime.memory_car_page = value

    def log(self, message):
        return self.runtime.log(message)

    def _call(self, service_name, method_name, *args, **kwargs):
        direct = getattr(self.runtime, method_name, None)
        if callable(direct):
            return direct(*args, **kwargs)
        service = getattr(self.runtime, service_name)
        return getattr(service, method_name)(*args, **kwargs)

    def update_running_ui(self, task_name="", current_val=0, max_val=0):
        return self.runtime.update_running_ui(task_name, current_val, max_val)

    def enter_menu(self):
        return self._call("recovery", "enter_menu")

    def check_pause(self):
        return self.runtime.check_pause()

    def check_vramne_during_race(self):
        return self._call("recovery", "check_vramne_during_race")

    def hw_press(self, key, delay=0.08):
        return self.runtime.hw_press(key, delay=delay)

    def hw_key_down(self, key):
        return self.runtime.hw_key_down(key)

    def hw_key_up(self, key):
        return self.runtime.hw_key_up(key)

    def game_click(self, pos, double=False):
        return self.runtime.game_click(pos, double=double)

    def move_to_game_coord(self, x, y):
        return self.runtime.move_to_game_coord(x, y)

    def wait_for_image(self, template_path, **kwargs):
        return self._call("vision", "wait_for_image", template_path, **kwargs)

    def wait_for_any_image(self, image_list, **kwargs):
        return self._call("vision", "wait_for_any_image", image_list, **kwargs)

    def wait_for_image_gray(self, template_path, **kwargs):
        return self._call("vision", "wait_for_image_gray", template_path, **kwargs)

    def wait_for_any_image_gray(self, image_list, **kwargs):
        return self._call("vision", "wait_for_any_image_gray", image_list, **kwargs)

    def find_image_gray(self, template_path, **kwargs):
        return self._call("vision", "find_image_gray", template_path, **kwargs)

    def find_any_image_gray(self, image_list, **kwargs):
        return self._call("vision", "find_any_image_gray", image_list, **kwargs)

    def wait_for_image_transparent(self, template_path, **kwargs):
        return self._call("vision", "wait_for_image_transparent", template_path, **kwargs)

    def wait_for_image_with_element_multi(self, main_path, sub_path, **kwargs):
        return self._call("vision", "wait_for_image_with_element_multi", main_path, sub_path, **kwargs)

    def wait_for_image_ultimate_safe(self, **kwargs):
        return self._call("vision", "wait_for_image_ultimate_safe", **kwargs)


def ensure_automation_context(value):
    if isinstance(value, AutomationContext):
        return value
    return AutomationContext(value)
