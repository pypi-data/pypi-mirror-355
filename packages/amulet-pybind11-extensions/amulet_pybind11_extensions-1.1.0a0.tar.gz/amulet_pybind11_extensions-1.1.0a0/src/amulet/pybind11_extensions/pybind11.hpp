#pragma once

#include <pybind11/pybind11.h>

namespace Amulet {
namespace pybind11_extensions {
    inline void keep_alive(pybind11::handle nurse, pybind11::handle patient){
        pybind11::detail::keep_alive_impl(nurse, patient);
    }

    template <typename T>
    inline bool is_class_bound(){
        return pybind11::detail::get_type_info(typeid(T));
    }
} // namespace pybind11_extensions
} // namespace Amulet
