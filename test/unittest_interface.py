from logilab.common.testlib import TestCase, unittest_main
from logilab.common.interface import *

class IFace1(Interface): pass
class IFace2(Interface): pass
class IFace3(Interface): pass


class A(object):
    __implements__ = (IFace1,)


class B(A): pass


class C1(B):
    __implements__ = list(B.__implements__) + [IFace3]
    
class C2(B):
    __implements__ = B.__implements__ + (IFace2,)
    
class D(C1):
    __implements__ = ()


class ExtendTC(TestCase):

    def setUp(self):
        global aimpl, c1impl, c2impl, dimpl
        aimpl = A.__implements__
        c1impl = C1.__implements__
        c2impl = C2.__implements__
        dimpl = D.__implements__
        
    def test_base(self):
        extend(A, IFace1)
        self.failUnless(A.__implements__ is aimpl)
        extend(A, IFace2)
        self.failUnlessEqual(A.__implements__, (IFace1, IFace2))  
        self.failUnlessEqual(B.__implements__, (IFace1, IFace2))
        self.failUnless(B.__implements__ is A.__implements__)
        self.failUnlessEqual(C1.__implements__, [IFace1, IFace3, IFace2])
        self.failUnlessEqual(C2.__implements__, (IFace1, IFace2))
        self.failUnless(C2.__implements__ is c2impl)
        self.failUnlessEqual(D.__implements__, (IFace2,))

    def test_notimpl_explicit(self):
        extend(C1, IFace3)
        self.failUnless(C1.__implements__ is c1impl)
        self.failUnless(D.__implements__ is dimpl)
        

if __name__ == '__main__':
    unittest_main()
