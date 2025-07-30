from mlc_tools.core.class_ import Class
from mlc_tools.core.function import Function
from mlc_tools.core.object import Object, Objects, AccessSpecifier


class GeneratorRefCounter(object):

    def __init__(self):
        pass

    def generate(self, model):
        if not model.generate_ref_counter:
            return

        for cls in model.classes:
            if not cls.superclasses and cls.type != 'enum':
                self._add(cls)

    @staticmethod
    def _add(cls: Class):
        if not cls.has_member_with_name('_reference_counter'):
            ref_counter = Object()
            ref_counter.name = '_reference_counter'
            ref_counter.type = 'std::atomic<int>'
            ref_counter.initial_value = '1'
            ref_counter.is_runtime = True
            ref_counter.access = AccessSpecifier.private
            cls.members.append(ref_counter)

            mutex = Object()
            mutex.name = '_ref_mutex'
            mutex.type = 'std::mutex'
            mutex.is_runtime = True
            mutex.access = AccessSpecifier.private
            cls.members.append(mutex)
        if not cls.has_method_with_name('retain'):
            retain = Function()
            retain.name = 'retain'
            retain.return_type = Objects.VOID
            retain.operations.append('std::lock_guard<std::mutex> lock(_ref_mutex);')
            retain.operations.append('_reference_counter.fetch_add(1, std::memory_order_relaxed);')
            # retain.operations.append('return _reference_counter;')
            cls.functions.append(retain)
        if not cls.has_method_with_name('release'):
            release = Function()
            release.name = 'release'
            release.return_type = Objects.INT
            release.operations.append('std::lock_guard<std::mutex> lock(_ref_mutex);')
            release.operations.append('auto ret = _reference_counter.fetch_sub(1, std::memory_order_acq_rel);')
            release.operations.append('if (ret == 1)')
            release.operations.append('{')
            release.operations.append('delete this;')
            release.operations.append('}')
            release.operations.append('return ret;')
            cls.functions.append(release)
