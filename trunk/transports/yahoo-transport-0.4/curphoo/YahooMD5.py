# YahooMD5.py
#
# gaim
#
# Some code copyright (C) 1998-1999, Mark Spencer <markster@marko.net>
# libfaim code copyright 1998, 1999 Adam Fritzler <afritz@auk.cx>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#

# Python port for the curphoo/xmpp.py project
#   by Norman Rasmussen <norman@rasmussen.co.za>

# The curphoo_process_auth code comes from the GAIM project.

from __future__ import generators
import md5,pysha,sha
from array import array
from string import maketrans
from yahoo_fn import yahoo_xfrm
from md5crypt import md5crypt

base64translate = maketrans('+/=', '._-')

alphabet1 = 'FBZDWAGHrJTLMNOPpRSKUVEXYChImkwQ'
alphabet2 = 'F0E1D2C3B4A59687abcdefghijklmnop'

challenge_lookup    = 'qzec2tb3um1olpar8whx4dfgijknsvy5'
operand_lookup      = '+|&%/*^-'
delimit_lookup      = ',;'

def curphoo_process_auth(username, password, seed):

    #
    # Magic: Phase 1.  Generate what seems to be a 30
    # byte value (could change if base64
    # ends up differently?  I don't remember and I'm
    # tired, so use a 64 byte buffer.
    #

    magic1 = []
    for char in seed:
        # Ignore parentheses.
        if char == '(' or char == ')': continue
        # Characters and digits verify against the challenge lookup.
        if char.isalpha() or char.isdigit():
            magic_work = challenge_lookup.index(char) << 3
        else:
            local_store = operand_lookup.index(char)
            magic1.append(magic_work | local_store)

    # Magic: Phase 2.  Take generated magic value and
    # sprinkle fairy dust on the values.

    magic2 = []
    for c in range(len(magic1)-1,0,-1):
        byte1 = magic1[c-1]
        byte2 = magic1[c]

        byte1 *= 0xcd
        byte1 &= 0xff
        byte1 ^= byte2

        magic2.append(byte1)

    # Magic: Phase 3.  This computes 20 bytes.  The first 4 bytes are used as our magic
    # key (and may be changed later); the next 16 bytes are an MD5 sum of the magic key
    # plus 3 bytes.  The 3 bytes are found by looping, and they represent the offsets
    # into particular functions we'll later call to potentially alter the magic key.

    comparison_src = array('B')
    while len(magic2) > 0 and len(comparison_src) < 20:
        cl = magic2.pop()

        if cl > 0x7f:
            if cl < 0xe0:
                bl = (cl & 0x1f) << 6
            else:
                bl = magic2.pop()
                cl = (cl & 0x0f) << 6
                bl = ((bl & 0x3f) + cl) << 6
            cl = magic2.pop()
            cl = (cl & 0x3f) + bl

        comparison_src.append(cl >> 8)
        comparison_src.append(cl & 0xff)

    # Compute values for recursive function table!
    def find_table_depth_values(md5root, search_hash):
        def guesser():
            yield(3,88) # take a wild guess at what seems to be a constant
            for i in range(0xffff):
                for j in range(5):
                    yield (j,i)
        for (j,i) in guesser():
            md5object = md5root.copy()
            md5object.update(chr(i & 0xff) + chr(i >> 8) + chr(j))
            if md5object.digest() == search_hash:
                return (j,i)
    (table,depth) = find_table_depth_values(md5.new(comparison_src[:4]), comparison_src[4:].tostring())

    # Transform magic_key_char using transform table
    x = comparison_src[3] << 24l | comparison_src[2] << 16 | comparison_src[1] << 8 | comparison_src[0]
    x = yahoo_xfrm( table, depth, x )
    x = yahoo_xfrm( table, depth, x )
    magic_key_char = chr(x & 0xFF) + chr(x >> 8 & 0xFF) + chr(x >> 16 & 0xFF) + chr(x >> 24 & 0xFF)

    crypt_result = md5crypt(password, '$1$_2S43d5f$')

    def finalstep(input, magic_key_char, table):

        def finalxor(hash, mask):
            result = array('B')
            for c in hash:
                result.append(ord(c) ^ mask)
            for c in range(64-len(hash)):
                result.append(mask)
            return result.tostring()

        hash = md5.new(input).digest().encode('base64').translate(base64translate, '\r\n')

        if (table >= 3): # We have to use the slow sha1 implementation to get to it's internals
            sha1 = pysha.new(finalxor(hash, 0x36) + magic_key_char)
            sha1.count[1] = sha1.count[1] - 1
        else:
            sha1 = sha.new(finalxor(hash, 0x36) + magic_key_char)
        digest1 = sha1.digest()
        digest2 = sha.new(finalxor(hash, 0x5c) + digest1).digest()

        result = ''
        for i in range(10):
            # First two bytes of digest stuffed together.
            val = (ord(digest2[i * 2]) << 8) + ord(digest2[i*2+1])

            result += alphabet1[(val >> 0x0b) & 0x1f] + '='
            result += alphabet2[(val >> 0x06) & 0x1f]
            result += alphabet2[(val >> 0x01) & 0x1f]
            result += delimit_lookup[val & 0x01]
        return result

    return (finalstep(password, magic_key_char, table), finalstep(crypt_result, magic_key_char, table))

if __name__ == '__main__':

    def test(user, pwd, chal, str1true, str2true):
        print ''
        print "user: '%s'"% user
        print "pass: '%s'"% pwd
        print "chal: '%s'"% chal

        (str1,str2) = curphoo_process_auth(user, pwd, chal)

        status1 = 'FAILED'
        status2 = 'FAILED'
        if str1true == str1: status1 = 'PASSED'
        if str2true == str2: status2 = 'PASSED'

        print "str1: '%s' (%s)"%( str1, status1)
        print "str2: '%s' (%s)"%( str2, status2)

    test_cases = (
        ('username' , 'password', 'f%g|8%(p+4+f*l&h|d-h*(g^d*q^2&w+o+(x&i/o+4-3)/s^(d|j+j-a*3^u|(4&q%x))))', 'P=42,Q=1A;I=0B;Y=68,U=E9;L=2B;m=hf,K=34;m=id;J=5g,', 'w=8e;r=pl,H=bg;I=62,U=gA,A=36;O=F2,r=b0;P=ii,h=in;'),
        ('myuser'   , 'mypass'  , 'f%g|8%(p+4+f*l&h|d-h*(g^d*q^2&w+o+(x&i/o+4-3)/s^(d|j+j-a*3^u|(4&q%x))))', 'G=Ai,p=6B,W=f6,I=BB,I=CC;V=bp;P=17,p=ee;r=mj;p=eA;', 'k=8c,h=8h,Y=Eb;W=oo,h=jh,K=cd,J=6m,r=Fd;W=l2;Q=pi;'),
        ('username' , 'password', 'g*g/3&5-k-(4/i/c*d^v|r^m&s%2+(z*v%j%q|l-h+v|t^(b&4-q|2)|n)/8*l|z&x%v)'  , 'O=Cg,r=pb,N=bp,O=Fn;F=e8;F=33;p=l9;S=bj,m=A0;p=ci,', 'p=Bh,O=D1,T=f0;D=0B;G=ag;H=na,C=cB,E=4F;T=fg;A=2j;'),
        ('myuser'   , 'mypass'  , 'g*g/3&5-k-(4/i/c*d^v|r^m&s%2+(z*v%j%q|l-h+v|t^(b&4-q|2)|n)/8*l|z&x%v)'  , 'J=C9,w=1j,F=An,A=pg,D=AE;L=E7;P=lk;N=F0,Y=28,R=EC,', 'O=kf,r=4C;D=b9;J=nf,r=EC;E=2F;w=c4;k=em,G=8A,S=dE;'),
        ('username' , 'password', '2&k%(1%k-i+m/o/u)*v-k|g-a%h|5-g%z*(8-(h|4|q-e+(a%5&w)+r/d%a+(q&a%g+s%e)))', 'S=2l,C=2e,V=Co,O=72,Y=oD,X=B9,E=l4,A=0n,h=3E;m=47;', 'S=2a;E=ap;k=m1,O=cA;w=bd,V=Ae,Q=dC;C=Fp;h=iF;M=7B,'),
        ('myuser'   , 'mypass'  , '2&k%(1%k-i+m/o/u)*v-k|g-a%h|5-g%z*(8-(h|4|q-e+(a%5&w)+r/d%a+(q&a%g+s%e)))', 'U=A5;r=a6;V=pF,T=ke;H=e8,w=g7,Q=9e;p=ci,m=60,r=3e,', 'k=FF;A=gh;Q=dm;W=j7;k=Ab,I=27,F=1d;X=nm;S=CF;w=1E,'),
        ('username' , 'password', 'p/x*c&o/u+5^(v/e/8%o|d)%u-u|(v)-i/p&(q|r&e/v*r&(e+b|8^5^w*o^5%e/w)/f|l)', 'U=c2;A=g4;X=iD,h=6o,I=m6,M=Ee;p=1c,C=p6;J=pg;B=el,', 'p=o8,Y=a5;B=fd,C=ck,N=7f,h=5d,r=36,I=C8,R=bo,C=6j;'),
        ('myuser'   , 'mypass'  , 'p/x*c&o/u+5^(v/e/8%o|d)%u-u|(v)-i/p&(q|r&e/v*r&(e+b|8^5^w*o^5%e/w)/f|l)', 'W=md;k=c3;A=Ai;k=fo;A=ba,L=A9;L=ne,I=3e;D=6C;W=f1,', 'T=hi;k=B0,W=c6;T=62,h=dC;r=DA;p=hD;J=99,h=4i,X=98,'),
    )

    for user, pwd, chal, str1true, str2true in test_cases:
        test(user, pwd, chal, str1true, str2true)
