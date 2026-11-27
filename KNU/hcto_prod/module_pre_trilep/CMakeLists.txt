# HcToWA analysis module (B2G-25-013 -> 2024), auto-detected as *_Analyzers.
sknano_add_analysis_module(
    NAME HcToWA
    HEADERS
        include/HcToWA/HcToWABase.h
        include/HcToWA/DiLepton.h
        include/HcToWA/Skim_TriLep.h
        include/HcToWA/MuonTnPProducer.h
        include/HcToWA/ElectronTnPProducer.h
        include/HcToWA/MeasTrigEff.h
        include/HcToWA/MeasFakeRate.h
        include/HcToWA/Skim_FakeRate.h
        include/HcToWA/ClosFakeRate.h
    SOURCES
        src/HcToWABase.cc
        src/DiLepton.cc
        src/Skim_TriLep.cc
        src/MuonTnPProducer.cc
        src/ElectronTnPProducer.cc
        src/MeasTrigEff.cc
        src/MeasFakeRate.cc
        src/Skim_FakeRate.cc
        src/ClosFakeRate.cc
    LINKDEF include/HcToWA/LinkDef.hpp
    INCLUDE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/include
    ANALYZERS DiLepton Skim_TriLep MuonTnPProducer ElectronTnPProducer MeasTrigEff MeasFakeRate Skim_FakeRate ClosFakeRate)
