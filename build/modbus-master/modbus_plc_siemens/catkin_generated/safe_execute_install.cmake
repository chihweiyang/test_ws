execute_process(COMMAND "/home/weber/test_ws/build/modbus-master/modbus_plc_siemens/catkin_generated/python_distutils_install.sh" RESULT_VARIABLE res)

if(NOT res EQUAL 0)
  message(FATAL_ERROR "execute_process(/home/weber/test_ws/build/modbus-master/modbus_plc_siemens/catkin_generated/python_distutils_install.sh) returned error code ")
endif()
