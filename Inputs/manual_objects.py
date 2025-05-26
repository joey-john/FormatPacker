from point_object import PointObject, GroupObjectList

def ManualInput() -> list[PointObject|GroupObjectList]:
    """ Create Manual Test Input Date - Can use to test Groupings. 
    
    Also called by test_FormatPacker to validate results
    """
    # Individual Point Objects
    A       = PointObject("A", 32, 32, offset=8)
    B       = PointObject("B", 16, 32, start_frame=4)
    C       = PointObject("C", 16, 16, start_frame=3)
    D       = PointObject("D", 8, 16, start_frame=1)
    E       = PointObject("E", 32, 32, start_frame=31)
    F       = PointObject("F", 16, 32, start_frame=4, offset=16)
    G       = PointObject("G", 8, 1)
    H       = PointObject("H", 64, 1, start_frame=1)
    I       = PointObject("I", 64, 32, start_frame=1)
    J       = PointObject("J", 16, 8, start_frame=1)
    K       = PointObject("K", 64, 16, start_frame=5)
    L       = PointObject("L", 64, 32)
    M       = PointObject("M", 32, 32, start_frame=1)
    N       = PointObject("N", 64, 2)
    O       = PointObject("O", 16, 2, start_frame=1)
    P       = PointObject("P", 64, 32)
    Q       = PointObject("Q", 32, 1, start_frame=1)
    R       = PointObject("R", 64, 4)
    S       = PointObject("S", 64, 32)
    T       = PointObject("T", 64, 1, start_frame=1)
    U       = PointObject("U", 8, 16)
    V       = PointObject("V", 8, 1)
    W       = PointObject("W", 3, 16)
    X       = PointObject("X", 16, 8, offset=256)
    Y       = PointObject("Y", 8, 2, start_frame=1)
    Z       = PointObject("Z", 8, 4)
    AA      = PointObject("AA", 8, 1, start_frame=1)
    BB      = PointObject("BB", 64, 16)
    CC      = PointObject("CC", 64, 16, start_frame=3)
    DD      = PointObject("DD", 32, 2, start_frame=1)
    EE      = PointObject("EE", 8, 8)
    FF      = PointObject("FF", 8, 4)
    GG      = PointObject("GG", 8, 4, start_frame=2)
    HH      = PointObject("HH", 8, 1, start_frame=1)
    II      = PointObject("II", 64, 2, start_frame=1)
    JJ      = PointObject("JJ", 64, 16)
    KK      = PointObject("KK", 8, 2, start_frame=1)
    LL      = PointObject("LL", 16, 2)
    MM      = PointObject("MM", 32, 4, start_frame=1)
    NN      = PointObject("NN", 16, 2)
    OO      = PointObject("OO", 32, 1, start_frame=4)
    PP      = PointObject("PP", 64, 1, start_frame=1)
    QQ      = PointObject("QQ", 32, 16)
    RR      = PointObject("RR", 64, 4)
    SS      = PointObject("SS", 64, 32)
    TT      = PointObject("TT", 64, 16, start_frame=1)
    UU      = PointObject("UU", 8, 2)
    VV      = PointObject("VV", 16, 2, start_frame=1)
    WW      = PointObject("WW", 32, 32)
    XX      = PointObject("XX", 1000, 16, start_frame=1)
    YY      = PointObject("YY", 8, 4, start_frame=1)
    ZZ      = PointObject("ZZ", 64, 2)
    AAA     = PointObject("AAA", 16, 4, start_frame=1)
    BBB     = PointObject("BBB", 64, 32, start_frame=2, offset=4)
    CCC     = PointObject("CCC", 8, 4, start_frame=1)
    DDD     = PointObject("DDD", 32, 32)
    EEE     = PointObject("EEE", 8, 8, start_frame=1)
    FFF     = PointObject("FFF", 8, 4)
    GGG     = PointObject("GGG", 16, 1)
    HHH     = PointObject("HHH", 8, 1)
    III     = PointObject("III", 64, 8)
    JJJ     = PointObject("JJJ", 32, 4)
    KKK     = PointObject("KKK", 32, 1)
    LLL     = PointObject("LLL", 32, 4)
    MMM     = PointObject("MMM", 32, 4, start_frame=1)
    NNN     = PointObject("NNN", 8, 8)
    OOO     = PointObject("OOO", 32, 2)
    PPP     = PointObject("PPP", 16, 16, start_frame=1)
    QQQ     = PointObject("QQQ", 8, 16, offset=32)
    RRR     = PointObject("RRR", 16, 1, start_frame=1)
    SSS     = PointObject("SSS", 8, 8, start_frame=3)
    TTT     = PointObject("TTT", 8, 1, start_frame=1)
    UUU     = PointObject("UUU", 16, 2, start_frame=1)
    VVV     = PointObject("VVV", 8, 1)
    WWW     = PointObject("WWW", 64, 2, start_frame=1)
    XXX     = PointObject("XXX", 32, 32, start_frame=1)
    YYY     = PointObject("YYY", 64, 2, start_frame=8)
    ZZZZ    = PointObject("ZZZZ", 32, 1, start_frame=1)
    AAAAA   = PointObject("AAAAA", 48, 1, start_frame=8, offset=16)
    
    # Group Created From Points
    group_ABC = GroupObjectList(16, A, B, C, name="group_ABC", start_frame=1, offset=8)
    group_BBB_CCC = GroupObjectList(32, BBB, CCC, name="group_BBB_CCC", start_frame=2, offset=4)
    group_XY = GroupObjectList(32, X, Y, name="group_XY",offset=256)
    
    # Objects List
    objects = [
        D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, Z, 
        AA, BB, CC, DD, EE, FF, GG, HH, II, JJ, KK, LL, MM, NN, OO, PP, QQ, RR, SS, TT, UU, VV, WW, XX, YY, ZZ, 
        AAA, DDD, EEE, FFF, GGG, HHH, III, JJJ, KKK, LLL, MMM, NNN, OOO, PPP, QQQ, RRR, SSS, TTT, UUU, VVV, WWW, XXX, YYY, ZZZZ, 
        AAAAA,

        group_ABC,
        group_XY,
        group_BBB_CCC,
    ]
    
    return objects