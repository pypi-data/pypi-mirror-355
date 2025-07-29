#pragma once

#include <pybind11/pybind11.h>

#include <algorithm>
#include <cstddef>
#include <memory>

#include <amulet/pybind11_extensions/collections.hpp>
#include <amulet/pybind11_extensions/iterator.hpp>

namespace detail {
// An iterator for the collections.abc.Sequence protocol.
class SequenceIterator {
private:
    pybind11::object obj;
    size_t index;
    std::ptrdiff_t step;

public:
    SequenceIterator(
        pybind11::object obj,
        size_t start,
        std::ptrdiff_t step)
        : obj(obj)
        , index(start)
        , step(step)
    {
    }

    pybind11::object next()
    {
        if (index < 0 || pybind11::len(obj) <= index) {
            throw pybind11::stop_iteration("");
        }
        pybind11::object item = obj.attr("__getitem__")(index);
        index += step;
        return item;
    }
};
}

namespace Amulet {
namespace pybind11_extensions {
    namespace collections {

        template <typename clsT>
        void def_Sequence_getitem_slice(clsT cls)
        {
            cls.def(
                "__getitem__",
                [](pybind11::object self, const pybind11::slice& slice) {
                    size_t start = 0, stop = 0, step = 0, slicelength = 0;
                    if (!slice.compute(pybind11::len(self), &start, &stop, &step, &slicelength)) {
                        throw pybind11::error_already_set();
                    }
                    pybind11::list out(slicelength);
                    pybind11::object getitem = self.attr("__getitem__");
                    for (size_t i = 0; i < slicelength; ++i) {
                        out[i] = getitem(start);
                        start += step;
                    }
                    return out;
                });
        }

        template <typename clsT>
        void def_Sequence_contains(clsT cls)
        {
            cls.def(
                "__contains__",
                [](pybind11::object self, pybind11::object value) {
                    pybind11::iterator it = pybind11::iter(self);
                    while (it != pybind11::iterator::sentinel()) {
                        if (it->equal(value)) {
                            return true;
                        }
                        ++it;
                    }
                    return false;
                });
        }

        template <typename elemT = pybind11::object, typename clsT>
        void def_Sequence_iter(clsT cls)
        {
            cls.def(
                "__iter__",
                [](pybind11::object self) -> pybind11_extensions::collections::Iterator<elemT> {
                    return Amulet::pybind11_extensions::make_iterator(::detail::SequenceIterator(self, 0, 1));
                });
        }

        template <typename elemT = pybind11::object, typename clsT>
        void def_Sequence_reversed(clsT cls)
        {
            cls.def(
                "__reversed__",
                [](pybind11::object self) -> pybind11_extensions::collections::Iterator<elemT> {
                    return Amulet::pybind11_extensions::make_iterator(::detail::SequenceIterator(self, pybind11::len(self) - 1, -1));
                });
        }

        template <typename clsT>
        void def_Sequence_index(clsT cls)
        {
            cls.def(
                "index",
                [](pybind11::object self, pybind11::object value, Py_ssize_t s_start, Py_ssize_t s_stop) {
                    size_t size = pybind11::len(self);
                    size_t start;
                    size_t stop;
                    if (s_start < 0) {
                        start = std::max<Py_ssize_t>(0, size + s_start);
                    } else {
                        start = s_start;
                    }
                    if (s_stop < 0) {
                        stop = size + s_stop;
                    } else {
                        stop = s_stop;
                    }
                    pybind11::object getitem = self.attr("__getitem__");
                    while (start < stop) {
                        pybind11::object obj;
                        try {
                            obj = getitem(start);
                        } catch (pybind11::error_already_set& e) {
                            if (e.matches(PyExc_IndexError)) {
                                break;
                            } else {
                                throw;
                            }
                        }

                        if (value.equal(obj)) {
                            return start;
                        }

                        start++;
                    }
                    throw pybind11::value_error("");
                },
                pybind11::arg("value"), pybind11::arg("start") = 0, pybind11::arg("stop") = std::numeric_limits<Py_ssize_t>::max());
        }

        template <typename clsT>
        void def_Sequence_count(clsT cls)
        {
            cls.def(
                "count",
                [](pybind11::object self, pybind11::object value) {
                    size_t count = 0;
                    size_t size = pybind11::len(self);
                    pybind11::object getitem = self.attr("__getitem__");
                    for (size_t i = 0; i < size; ++i) {
                        if (value.equal(getitem(i))) {
                            count++;
                        }
                    }
                    return count;
                },
                pybind11::arg("value"));
        }

        template <typename clsT>
        void register_Sequence(clsT cls)
        {
            pybind11::module::import("collections.abc").attr("Sequence").attr("register")(cls);
        }
    } // namespace collections
} // namespace pybind11_extensions
} // namespace Amulet
