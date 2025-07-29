#pragma once
#include <pybind11/pybind11.h>

#include <amulet/pybind11_extensions/pybind11.hpp>
#include <amulet/pybind11_extensions/builtins.hpp>
#include <amulet/pybind11_extensions/collections.hpp>

namespace Amulet {
namespace pybind11_extensions {

    // Create a python iterator around a C++ class that implements method next()
    // Next must throw py::stop_iteration() to signal the end of the iterator.
    template <
        pybind11::return_value_policy Policy = pybind11::return_value_policy::automatic,
        typename Iterator,
        typename... Extra>
    auto make_iterator(Iterator it, Extra&&... extra) -> pybind11_extensions::collections::Iterator<decltype(it.next())>
    {
        if (!is_class_bound<Iterator>()) {
            pybind11::class_<Iterator>(pybind11::handle(), "iterator", pybind11::module_local())
                .def(
                    "__iter__",
                    [](
                        pybind11_extensions::PyObjectCpp<Iterator>& self) -> pybind11_extensions::PyObjectCpp<Iterator>& { return self; })
                .def(
                    "__next__",
                    [](Iterator& self) -> decltype(it.next()) {
                        return self.next();
                    },
                    std::forward<Extra>(extra)...,
                    Policy);
        }
        return pybind11::cast(std::forward<Iterator>(it));
    }

} // namespace pybind11_extensions
} // namespace Amulet
