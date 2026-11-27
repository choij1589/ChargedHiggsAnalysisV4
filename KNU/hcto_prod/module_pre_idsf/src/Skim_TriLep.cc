#include <HcToWA/Skim_TriLep.h>

#include <cmath>
#include <iostream>

Skim_TriLep::Skim_TriLep() {}
Skim_TriLep::~Skim_TriLep() {}

void Skim_TriLep::initializeAnalyzer() {
    selected_.clear();
    nSeen_ = 0;
}

void Skim_TriLep::executeEvent() {
    ++nSeen_;
    int nLep = 0;
    float lead = 0.f;
    for (const auto m : GetAllMuonViews()) {
        const float pt = m.MiniAODPt();
        if (pt <= kMinPt || std::fabs(m.Eta()) >= kMuonEta) continue;
        ++nLep;
        if (pt > lead) lead = pt;
    }
    for (const auto e : GetAllElectronViews()) {
        const float pt = e.MiniAODPt();
        if (pt <= kMinPt || std::fabs(e.Eta()) >= kElectronEta) continue;
        ++nLep;
        if (pt > lead) lead = pt;
    }
    if (nLep >= 3 && lead > kLeadPt) selected_.push_back(CurrentEntry());
}

void Skim_TriLep::WriteHist() {
    Hists().Fill("skim/nEvents", 0, static_cast<double>(nSeen_), 2, 0., 2.);
    Hists().Fill("skim/nEvents", 1, static_cast<double>(selected_.size()), 2, 0., 2.);
    std::cout << "[Skim_TriLep] selected " << selected_.size() << " / " << nSeen_ << " events" << std::endl;
    SnapshotSelectedInput(std::move(selected_), "Events");
    AnalyzerCore::WriteHist();
}
