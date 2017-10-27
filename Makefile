.DEFAULT_GOAL := all

# location of the Python header files
PYTHON_VERSION = 3.5
PYTHON_INCLUDE = /usr/include/python$(PYTHON_VERSION)

# location of the Boost Python include files and library
BOOST_PATH = /opt/cad/boost/1_65_1
BOOST_INC  = $(BOOST_PATH)/include
BOOST_LIB  = $(BOOST_PATH)/lib

TARGET = vframe

BUILD_DIR = build
OBJ_DIR   = $(BUILD_DIR)/obj
BIN_DIR   = bin
SRC_DIR   = src

FLAGS     = -ffunction-sections 
FLAGS    += -fdata-sections
#CFLAGS  = $(FLAGS)
CFLAGS = --std=c++11
LFLAGS = -Wl,--gc-sections

$(BIN_DIR)/$(TARGET).so: $(OBJ_DIR)/$(TARGET).o Makefile
	g++ -shared -Wl,--export-dynamic $(OBJ_DIR)/$(TARGET).o -L$(BOOST_LIB) -l:libboost_python3.so -lboost_numpy3 \
	-L/usr/lib/python3.5/config-3.5m-x86_64-linux-gnu -lpython$(PYTHON_VERSION)m -o $(BIN_DIR)/$(TARGET).so $(CFLAGS) $(FLAGS) $(LFLAGS)

$(OBJ_DIR)/$(TARGET).o: $(SRC_DIR)/$(TARGET).cpp Makefile
	g++ -I$(PYTHON_INCLUDE) -I$(BOOST_INC) -fPIC -c $(CFLAGS) $(FLAGS) -o $(OBJ_DIR)/$(TARGET).o $(SRC_DIR)/$(TARGET).cpp

all: $(BIN_DIR)/$(TARGET).so


