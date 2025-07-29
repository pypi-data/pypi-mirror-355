#pragma once

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/typing.h>

#include <variant>

#include <amulet/pybind11_extensions/builtins.hpp>
#include <amulet/pybind11_extensions/collections.hpp>
#include <amulet/pybind11_extensions/hash.hpp>
#include <amulet/pybind11_extensions/iterator.hpp>
#include <amulet/pybind11_extensions/types.hpp>

namespace Amulet {
namespace pybind11_extensions {
    namespace collections {
        template <typename clsT>
        void def_Mapping_repr(clsT cls)
        {
            cls.def(
                "__repr__",
                [](pybind11::object self) {
                    std::string repr = "{";
                    bool is_first = true;
                    for (auto it = self.begin(); it != self.end(); it++) {
                        if (is_first) {
                            is_first = false;
                        } else {
                            repr += ", ";
                        }
                        repr += pybind11::repr(*it);
                        repr += ": ";
                        repr += pybind11::repr(self.attr("__getitem__")(*it));
                    }
                    repr += "}";
                    return repr;
                });
        }

        template <typename KT = pybind11::object, typename clsT>
        void def_Mapping_contains(clsT cls)
        {
            cls.def(
                "__contains__",
                [](pybind11::object self, pybind11_extensions::PyObjectCpp<KT> key) {
                    try {
                        self.attr("__getitem__")(key);
                        return true;
                    } catch (const pybind11::error_already_set& e) {
                        if (e.matches(PyExc_KeyError)) {
                            return false;
                        } else {
                            throw;
                        }
                    }
                });
        }

        template <typename KT = pybind11::object, typename clsT>
        void def_Mapping_keys(clsT cls)
        {
            pybind11::object KeysView = pybind11::module::import("collections.abc").attr("KeysView");
            cls.def(
                "keys",
                [KeysView](pybind11::object self) -> pybind11_extensions::collections::KeysView<KT> { return KeysView(self); });
        }

        template <typename VT = pybind11::object, typename clsT>
        void def_Mapping_values(clsT cls)
        {
            pybind11::object ValuesView = pybind11::module::import("collections.abc").attr("ValuesView");
            cls.def(
                "values",
                [ValuesView](pybind11::object self) -> pybind11_extensions::collections::ValuesView<VT> { return ValuesView(self); });
        }

        template <typename KT = pybind11::object, typename VT = pybind11::object, typename clsT>
        void def_Mapping_items(clsT cls)
        {
            pybind11::object ItemsView = pybind11::module::import("collections.abc").attr("ItemsView");
            cls.def(
                "items",
                [ItemsView](pybind11::object self) -> pybind11_extensions::collections::ItemsView<KT, VT> { return ItemsView(self); });
        }

        template <typename KT = pybind11::object, typename VT = pybind11::object, typename clsT>
        void def_Mapping_get(clsT cls)
        {
            cls.def(
                "get",
                [](
                    pybind11::object self,
                    pybind11_extensions::PyObjectCpp<KT> key,
                    pybind11::typing::Optional<VT> default_) -> pybind11::typing::Optional<VT> {
                    try {
                        return self.attr("__getitem__")(key);
                    } catch (const pybind11::error_already_set& e) {
                        if (e.matches(PyExc_KeyError)) {
                            return default_;
                        } else {
                            throw;
                        }
                    }
                },
                pybind11::arg("key"),
                pybind11::arg("default") = pybind11::none());
        }

        template <typename clsT>
        void def_Mapping_eq(clsT cls)
        {
            pybind11::object dict = pybind11::module::import("builtins").attr("dict");
            pybind11::object isinstance = pybind11::module::import("builtins").attr("isinstance");
            pybind11::object NotImplemented = pybind11::module::import("builtins").attr("NotImplemented");
            pybind11::object PyMapping = pybind11::module::import("collections.abc").attr("Mapping");
            cls.def(
                "__eq__",
                [dict,
                    isinstance,
                    NotImplemented,
                    PyMapping](
                    pybind11::object self,
                    pybind11::object other) -> std::variant<bool, pybind11_extensions::types::NotImplementedType> {
                    if (!isinstance(other, PyMapping)) {
                        return NotImplemented;
                    }
                    return dict(self.attr("items")()).equal(dict(other.attr("items")()).cast<pybind11::dict>());
                });
        }

        template <typename clsT>
        void def_Mapping_hash(clsT cls)
        {
            Amulet::pybind11_extensions::def_unhashable(cls);
        }

        template <typename clsT>
        void register_Mapping(clsT cls)
        {
            pybind11::module::import("collections.abc").attr("Mapping").attr("register")(cls);
        }

    } // namespace collections

    namespace detail {
        template <typename Map>
        class MapWrapper {
        public:
            using MapType = Map;

            const Map& map;

            MapWrapper(const Map& map)
                : map(map)
            {
            }
        };

        template <typename Map, typename Owner>
        class OwningMapWrapper : public MapWrapper<Map> {
        private:
            Owner owner;

        public:
            OwningMapWrapper(const Map& map, Owner&& owner)
                : MapWrapper<Map>(map)
                , owner(std::forward<Owner>(owner))
            {
            }
        };

        template <typename Map>
        class MapIterator {
        private:
            const Map& map;
            typename Map::const_iterator begin;
            typename Map::const_iterator end;
            typename Map::const_iterator it;
            size_t size;

        public:
            MapIterator(const Map& map)
                : map(map)
                , begin(map.begin())
                , end(map.end())
                , it(map.begin())
                , size(map.size())
            {
            }

            pybind11::object next()
            {
                // This is not fool proof.
                // There are cases where this is true but the iterator is invalid.
                // The programmer should write good code and this will catch some of the bad cases.
                if (size != map.size() || begin != map.begin() || end != map.end()) {
                    throw std::runtime_error("map changed size during iteration.");
                }
                if (it == end) {
                    throw pybind11::stop_iteration("");
                }
                return pybind11::cast((it++)->first);
            }
        };
    } // namespace detail

    // Make a collections.abc.Iterator around a C++ map-like object.
    // The caller must tie the lifespan of the map to the lifespan of the returned object.
    template <typename Map>
    collections::Iterator<typename Map::key_type> make_map_iterator(const Map& map)
    {
        return make_iterator(detail::MapIterator(map));
    }

    namespace detail {
        template <typename MappingWrapper, typename Cls>
        void bind_mapping_to(Cls& Mapping)
        {
            Mapping.def(
                "__getitem__",
                [](MappingWrapper& self, pybind11::object key) {
                    try {
                        return pybind11::cast(self.map.at(key.cast<typename MappingWrapper::MapType::key_type>()));
                    } catch (const std::out_of_range&) {
                        throw pybind11::key_error(pybind11::repr(key));
                    }
                });
            Mapping.def(
                "__iter__",
                [](MappingWrapper& self) {
                    return make_map_iterator(self.map);
                },
                pybind11::keep_alive<0, 1>());
            Mapping.def(
                "__len__",
                [](MappingWrapper& self) {
                    return self.map.size();
                });
            Mapping.def(
                "__contains__",
                [](MappingWrapper& self, pybind11::object key) {
                    return self.map.contains(key.cast<typename MappingWrapper::MapType::key_type>());
                });
            collections::def_Mapping_repr(Mapping);
            collections::def_Mapping_keys(Mapping);
            collections::def_Mapping_values(Mapping);
            collections::def_Mapping_items(Mapping);
            collections::def_Mapping_get(Mapping);
            collections::def_Mapping_eq(Mapping);
            collections::def_Mapping_hash(Mapping);
            collections::register_Mapping(Mapping);
        }

        template <typename MappingWrapper>
        void bind_mapping()
        {
            pybind11::class_<MappingWrapper> Mapping(pybind11::handle(), "Mapping", pybind11::module_local());
            bind_mapping_to<MappingWrapper>(Mapping);
        }
    } // namespace detail

    // Make a python class that models collections.abc.Mapping around a C++ map-like object.
    // The caller must tie the lifespan of the map to the lifespan of the returned object.
    template <typename Map>
    collections::Mapping<typename Map::key_type, typename Map::mapped_type> make_mapping(const Map& map)
    {
        using MappingWrapper = detail::MapWrapper<Map>;
        if (!is_class_bound<MappingWrapper>()) {
            detail::bind_mapping<MappingWrapper>();
        }
        return pybind11::cast(MappingWrapper(map));
    }

    // Make a python class that models collections.abc.Mapping around a C++ map-like object.
    // Owner must keep the map alive until it is destroyed. It can be a smart pointer, py::object or any object keeping the map alive.
    template <typename Map, typename Owner>
    collections::Mapping<typename Map::key_type, typename Map::mapped_type> make_mapping(const Map& map, Owner&& owner)
    {
        using MappingWrapper = detail::OwningMapWrapper<Map, Owner>;
        if (!is_class_bound<MappingWrapper>()) {
            detail::bind_mapping<MappingWrapper>();
        }
        return pybind11::cast(MappingWrapper(map, std::forward<Owner>(owner)));
    }

} // namespace pybind11_extensions
} // namespace Amulet
