#include <HcToWA/GenLeptonType.h>

#include <TVector2.h>

#include <cmath>
#include <cstdlib>

namespace {
float DR(float eta1, float phi1, float eta2, float phi2) {
    const float de = eta1 - eta2;
    const float dp = static_cast<float>(TVector2::Phi_mpi_pi(phi1 - phi2));
    return std::sqrt(de * de + dp * dp);
}
} // namespace

bool GenLeptonType::IsSignalPID(int pid) {
    const int a = std::abs(pid);
    return a >= 9900000 || a == 36;
}

// {index of the first copy of the particle, index of the last copy of its mother}
void GenLeptonType::SelfHistory(int idx, int &firstCopy, int &mother) const {
    firstCopy = idx;
    mother = -1;
    if (idx < 2 || idx >= N()) return;
    const int pid = G(idx).PdgId();
    int cur = idx, mom = G(idx).MotherIndex();
    while (mom >= 0 && mom < N() && G(mom).PdgId() == pid) {
        cur = mom;
        mom = G(mom).MotherIndex();
    }
    firstCopy = cur;
    mother = (mom >= 0 && mom < N()) ? mom : -1;
}

bool GenLeptonType::IsFromHadron(int idx) const {
    if (idx < 2) return true;
    int start, mom;
    SelfHistory(idx, start, mom);
    if (mom < 0) return true;
    const int st = G(start).Status();
    if (st > 20 && st < 30) return false; // hard process
    int cur = start;
    while (true) {
        int f, m;
        SelfHistory(cur, f, m);
        if (m < 0) return true; // reached the initial partons
        cur = m;
        int curStart, curMom;
        SelfHistory(cur, curStart, curMom);
        const int pid = std::abs(G(cur).PdgId());
        const int startSt = G(curStart).Status();
        if (pid == 23 || pid == 24 || pid == 25 || pid == 6) return false;
        if (IsSignalPID(pid)) return false;
        if ((pid == 11 || pid == 13 || pid == 15 || pid == 22) && startSt > 20 && startSt < 30) return false;
        if (pid > 50) return true;
        if ((pid >= 1 && pid <= 5) || pid == 21) return true;
        if (cur < 2) return false; // old loop condition: the beams end the walk without a verdict
    }
}

bool GenLeptonType::FinalPhotonIsStatus23() const {
    if (st23Done_) return st23_;
    st23Done_ = true;
    bool isFinal23 = false, has23 = false;
    for (int i = 2; i < N(); ++i) {
        const auto gi = G(i);
        const int fpid = std::abs(gi.PdgId()), st = gi.Status(), mi = gi.MotherIndex();
        if (mi < 0 || mi >= N()) continue;
        const int mpid = G(mi).PdgId();
        if (!((fpid != 22 && mpid == 22) || (fpid == 22 && (st == 23 || st == 1)))) continue;
        int last, mom;
        SelfHistory(i, last, mom);
        const int lastSt = G(last).Status();
        int mStOrig = -1;
        if (mom != -1) {
            int ml, mm;
            SelfHistory(mom, ml, mm);
            mStOrig = G(ml).Status();
        }
        if (fpid == 22) {
            if (st == 23) {
                has23 = true;
                isFinal23 = true;
            } else if (st == 1 && lastSt == 23) {
                isFinal23 = false;
                break;
            }
        } else if (mpid == 22 && mStOrig == 23) {
            isFinal23 = false;
            break;
        }
    }
    st23_ = has23 && isFinal23;
    return st23_;
}

int GenLeptonType::TypeOfGen(int idx) const {
    if (idx < 2 || idx >= N()) return 0;
    if (G(idx).Status() != 1) return 0;
    const int apid = std::abs(G(idx).PdgId());
    if (!(apid == 11 || apid == 13)) return 0;

    int lastSelf, mother;
    SelfHistory(idx, lastSelf, mother);
    const int statusOrig = G(lastSelf).Status();
    const bool hadronic = IsFromHadron(idx);
    int mpid = 0, grmpid = 0, mStOrig = 0, mStLast = 0, grmStOrig = 0, grmStLast = 0, grMother = -1;
    if (mother != -1) {
        int lastM;
        SelfHistory(mother, lastM, grMother);
        mpid = std::abs(G(mother).PdgId());
        mStOrig = G(lastM).Status();
        mStLast = G(mother).Status();
    }
    if (grMother != -1) {
        int lastG, gg;
        SelfHistory(grMother, lastG, gg);
        grmpid = std::abs(G(grMother).PdgId());
        grmStOrig = G(lastG).Status();
        grmStLast = G(grMother).Status();
    }
    auto hard = [](int s) { return s > 20 && s < 30; };

    if (mpid == 23 || mpid == 24 || mpid == 25) return 1;
    if (IsSignalPID(mpid)) return 2;
    if (mpid == 37) return 6;
    if (hard(statusOrig)) return 1;
    if (mpid > 50) return -2;
    if (mpid == 15 && mStLast == 2) {
        if (grmpid == 23 || grmpid == 24 || grmpid == 25) return 3;
        if (IsSignalPID(grmpid)) return 3;
        if (hard(mStOrig)) return 3;
        if (hadronic) return -3;
        if (grmpid == 22 && hard(grmStOrig)) return 5;
        if (grmpid == 22) return 4;
        if ((grmpid == 11 || grmpid == 13 || grmpid == 15) && grmStLast != 2) return 4;
        return 0;
    }
    if (mpid == 22) {
        if (hard(mStOrig)) return 5;
        if (hadronic) return -4;
        if (grmpid == 24 || grmpid == 23 || grmpid == 6) return 4;
        if (grmpid == 11 || grmpid == 13 || grmpid == 15) return 4;
        return 0;
    }
    if ((mpid == 11 || mpid == 13 || mpid == 15) && mStLast != 2 && !hadronic) return 4;
    if (((mpid >= 1 && mpid <= 5) || mpid == 21) && mStLast != 2) return -4;
    if (mpid == 6) return 4;
    return 0;
}

int GenLeptonType::PhotonType(int idx) const {
    if (idx < 2 || idx >= N()) return 0;
    const auto gp = G(idx);
    if (!(gp.PdgId() == 22 && (gp.Status() == 1 || gp.Status() == 23))) return 0;
    if (gp.Status() == 23) return FinalPhotonIsStatus23() ? 1 : 0;
    int start, mom;
    SelfHistory(idx, start, mom);
    if (mom < 0) return 0;
    const int st = G(start).Status();
    const int mpid = std::abs(G(mom).PdgId());
    if (st > 20 && st < 30) return 1;
    if (mpid == 23 || mpid == 25) return 1;
    if (mpid == 24 || mpid == 6 || IsSignalPID(mpid)) return 2;
    if (IsFromHadron(idx)) return -2;
    if (mpid == 11 || mpid == 13 || mpid == 15) return 2;
    return 0;
}

int GenLeptonType::SameSCPromptElectronType(int idx) const {
    if (idx < 2 || std::abs(G(idx).PdgId()) != 11 || G(idx).Status() != 1) return -1;
    const float eta = G(idx).Eta(), phi = G(idx).Phi();
    int out = -1;
    for (int i = 2; i < N(); ++i) {
        const auto gi = G(i);
        if (gi.Status() != 1 || std::abs(gi.PdgId()) != 11) continue;
        if (std::fabs(eta - gi.Eta()) > 0.1f) continue;
        if (std::fabs(TVector2::Phi_mpi_pi(phi - gi.Phi())) > 0.3) continue;
        const int t = TypeOfGen(i);
        if (t >= 1 && t <= 3) out = t;
    }
    return out;
}

int GenLeptonType::MatchLepton(int absPdg, float eta, float phi) const {
    float best = 0.1f;
    int out = -1;
    for (int i = 2; i < N(); ++i) {
        const auto gi = G(i);
        if (gi.Status() != 1 || std::abs(gi.PdgId()) != absPdg || gi.MotherIndex() < 0) continue;
        const float d = DR(eta, phi, gi.Eta(), gi.Phi());
        if (d < best) {
            best = d;
            out = i;
        }
    }
    return out;
}

int GenLeptonType::MatchPhoton(float pt, float eta, float phi) const {
    float best = 0.2f;
    int out = -1;
    for (int i = 2; i < N(); ++i) {
        const auto gi = G(i);
        if (gi.MotherIndex() < 0) continue;
        if (!(std::abs(gi.PdgId()) == 22 && (gi.Status() == 1 || gi.Status() == 23))) continue;
        if (gi.Pt() < 10.f) continue;
        const float r = pt / gi.Pt();
        if (!(r > 0.5f && r < 1.5f)) continue;
        const float d = DR(eta, phi, gi.Eta(), gi.Phi());
        if (d > 0.2f) continue;
        if (gi.Status() == 23 && !FinalPhotonIsStatus23()) continue;
        if (d < best) {
            best = d;
            out = i;
        }
    }
    return out;
}

int GenLeptonType::Type(bool electron, float pt, float eta, float phi) const {
    if (!g_) return 0;
    const int m = MatchLepton(electron ? 11 : 13, eta, phi);
    if (m < 0) {
        const int ph = MatchPhoton(pt, eta, phi);
        const int pt_ = ph < 0 ? 0 : PhotonType(ph);
        if (pt_ == 1) return -5;
        if (pt_ == 2) return -6;
        return -1;
    }
    int t = TypeOfGen(m);
    if (t == 4 || t == 5) {
        const int near = SameSCPromptElectronType(m);
        if (near > 0) t = near;
    }
    return t;
}
