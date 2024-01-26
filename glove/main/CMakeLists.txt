
#
# Main component of TF Micro project 'micro_speech'.
#

idf_component_register(
    SRCS 
    main.cpp
    output_handler.cc
    # data_capture.cpp
    # main_classify.cpp
    # main.cc 
    # main_functions.cc constants.cc model.cc
    INCLUDE_DIRS ".")
