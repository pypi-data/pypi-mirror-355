#pragma once
#include <iterator>
#include <ranges>

#include <pybind11/pybind11.h>

// I have found cases where I want to accept or return a python object matching a collections.abc class.
// This extension adds subclasses of py::object with type hints for the collections.abc classes.
// This allows C++ functions to accept or return python objects that match the collection.abc classes.
// Note that these are handled in the same way as py::object thus there is no type validation.

namespace Amulet {
namespace pybind11_extensions {
    namespace collections {
        template <typename T>
        class Iterator : public pybind11::object {
        public:
            PYBIND11_OBJECT_DEFAULT(Iterator, object, PyIter_Check)

            using iterator_category = std::input_iterator_tag;
            using difference_type = pybind11::ssize_t;
            using value_type = T;

            Iterator& operator++()
            {
                advance();
                return *this;
            }

            Iterator operator++(int)
            {
                auto rv = *this;
                advance();
                return rv;
            }

            T operator*() const
            {
                return obj().template cast<T>();
            }

            std::unique_ptr<T> operator->() const
            {
                return std::make_unique<T>(obj().template cast<T>());
            }

            static Iterator sentinel() { return {}; }

            friend bool operator==(const Iterator& a, const Iterator& b) { return a.obj().ptr() == b.obj().ptr(); }
            friend bool operator!=(const Iterator& a, const Iterator& b) { return a.obj().ptr() != b.obj().ptr(); }

        private:
            void advance()
            {
                value = pybind11::reinterpret_steal<pybind11::object>(PyIter_Next(m_ptr));
                if (value.ptr() == nullptr && PyErr_Occurred()) {
                    throw pybind11::error_already_set();
                }
            }

            const pybind11::object& obj() const
            {
                if (m_ptr && !value.ptr()) {
                    auto& self = const_cast<Iterator&>(*this);
                    self.advance();
                }
                return value;
            }

        private:
            pybind11::object value = {};
        };
        static_assert(std::input_iterator<Iterator<int>>);

        template <typename T>
        class Iterable : public pybind11::object {
            PYBIND11_OBJECT_DEFAULT(Iterable, object, pybind11::detail::PyIterable_Check)

            Iterator<T> begin() const
            {
                return Iterator<T>(pybind11::object::begin());
            }
            Iterator<T> end() const
            {
                return Iterator<T>(pybind11::object::end());
            }
        };
        static_assert(std::ranges::input_range<Iterable<int>>);
        static_assert(std::convertible_to<std::ranges::range_value_t<Iterable<int>>, const int&>);

        template <typename T>
        class Sequence : public pybind11::object {
            PYBIND11_OBJECT_DEFAULT(Sequence, object, PySequence_Check)

            Iterator<T> begin() const
            {
                return Iterator<T>(pybind11::object::begin());
            }

            Iterator<T> end() const
            {
                return Iterator<T>(pybind11::object::end());
            }

            Py_ssize_t size() const
            {
                return PyObject_Size(ptr());
            }
        };

        template <typename K, typename V>
        class Mapping : public pybind11::object {
            PYBIND11_OBJECT_DEFAULT(Mapping, object, PyMapping_Check)
        };

        template <typename K, typename V>
        class MutableMapping : public pybind11::object {
            PYBIND11_OBJECT_DEFAULT(MutableMapping, object, PyMapping_Check)
        };

        template <typename K>
        class KeysView : public pybind11::object {
            PYBIND11_OBJECT_DEFAULT(KeysView, object, PyObject_Type)
        };

        template <typename V>
        class ValuesView : public pybind11::object {
            PYBIND11_OBJECT_DEFAULT(ValuesView, object, PyObject_Type)
        };

        template <typename K, typename V>
        class ItemsView : public pybind11::object {
            PYBIND11_OBJECT_DEFAULT(ItemsView, object, PyObject_Type)
        };
    } // namespace collections
} // namespace pybind11_extensions
} // namespace Amulet

namespace pybind11 {
namespace detail {
    template <typename T>
    struct handle_type_name<Amulet::pybind11_extensions::collections::Iterator<T>> {
        static constexpr auto name = const_name("collections.abc.Iterator[") + make_caster<T>::name + const_name("]");
    };

    template <typename T>
    struct handle_type_name<Amulet::pybind11_extensions::collections::Iterable<T>> {
        static constexpr auto name = const_name("collections.abc.Iterable[") + make_caster<T>::name + const_name("]");
    };

    template <typename T>
    struct handle_type_name<Amulet::pybind11_extensions::collections::Sequence<T>> {
        static constexpr auto name = const_name("collections.abc.Sequence[") + make_caster<T>::name + const_name("]");
    };

    template <typename K, typename V>
    struct handle_type_name<Amulet::pybind11_extensions::collections::Mapping<K, V>> {
        static constexpr auto name = const_name("collections.abc.Mapping[") + make_caster<K>::name + const_name(", ") + make_caster<V>::name + const_name("]");
    };

    template <typename K, typename V>
    struct handle_type_name<Amulet::pybind11_extensions::collections::MutableMapping<K, V>> {
        static constexpr auto name = const_name("collections.abc.MutableMapping[") + make_caster<K>::name + const_name(", ")
            + make_caster<V>::name + const_name("]");
    };

    template <typename K>
    struct handle_type_name<Amulet::pybind11_extensions::collections::KeysView<K>> {
        static constexpr auto name = const_name("collections.abc.KeysView[") + make_caster<K>::name + const_name("]");
    };

    template <typename V>
    struct handle_type_name<Amulet::pybind11_extensions::collections::ValuesView<V>> {
        static constexpr auto name = const_name("collections.abc.ValuesView[") + make_caster<V>::name + const_name("]");
    };

    template <typename K, typename V>
    struct handle_type_name<Amulet::pybind11_extensions::collections::ItemsView<K, V>> {
        static constexpr auto name = const_name("collections.abc.ItemsView[") + make_caster<K>::name + const_name(", ")
            + make_caster<V>::name + const_name("]");
    };
}
}
