.DEFAULT_GOAL := all

# location of the Python header files
PYTHON_VERSION = 3.5
PYTHON_INCLUDE = /usr/include/python$(PYTHON_VERSION)

# location of the Boost Python include files and library
BOOST_PATH = /opt/cad/boost/1_65_1
BOOST_INC  = $(BOOST_PATH)/include
BOOST_LIB  = $(BOOST_PATH)/lib

TARGET = slon

FLAGS     = -ffunction-sections 
FLAGS    += -fdata-sections
#CFLAGS  = $(FLAGS)
CFLAGS = --std=c++11
LFLAGS = -Wl,--gc-sections

$(TARGET).so: $(TARGET).o Makefile
	g++ -shared -Wl,--export-dynamic $(TARGET).o -L$(BOOST_LIB) -l:libboost_python3.so -lboost_numpy3 \
	-L/usr/lib/python3.5/config-3.5m-x86_64-linux-gnu -lpython$(PYTHON_VERSION)m -o $(TARGET).so $(CFLAGS) $(FLAGS) $(LFLAGS)

$(TARGET).o: $(TARGET).cpp Makefile
	g++ -I$(PYTHON_INCLUDE) -I$(BOOST_INC) -fPIC -c $(TARGET).cpp $(CFLAGS) $(FLAGS)

all: $(TARGET).so


