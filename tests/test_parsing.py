from fractions import Fraction
import pytest
from gsm8k_lab.parsing import numeric, answer_field, code_output, extract_code, arithmetic, FormatError, ResourceError

@pytest.mark.parametrize('s,v',[('$1,200.00','1200'),('3/2','1.5'),('-0.5','-1/2'),('£ 2','2'),('.25','1/4')])
def test_exact_normalization(s,v):
    assert numeric(s)==numeric(v)

@pytest.mark.parametrize('s',['The answer is 12','1,00','12 dollars','50%','nan','inf','1e3','1/0','1 2','(2)','True','0x10','1_000','2\n3'])
def test_reject_ambiguous(s):
    with pytest.raises((FormatError,ResourceError)):numeric(s)

def test_no_broad_tolerance():
    assert numeric('0.3333333333')!=numeric('1/3')

def test_explicit_final():
    assert answer_field('We use 7 and 2.\nFINAL: 3.5')==Fraction(7,2)
    for s in ['reason 7 then 2','FINAL: 2\nFINAL: 2','FINAL: 2\nextra','result FINAL: 2']:
        with pytest.raises(FormatError):answer_field(s)
    with pytest.raises(FormatError):code_output('debug 2\nFINAL: 2')

def test_arithmetic_exact_and_bounded():
    assert arithmetic('(0.1 + 0.2) / 0.3')==1
    assert arithmetic('2 ** -3')==Fraction(1,8)
    for expression in ['__import__("os").system("id")','[1][0]','True','sum([1,2])','x+1','(1).__class__']:
        with pytest.raises(FormatError):arithmetic(expression)
    for expression in ['2**999999','10**12*10**12*10**12','1+'*1000+'1']:
        with pytest.raises(ResourceError):arithmetic(expression)

def test_code_extraction_no_repair():
    assert extract_code('```python\nprint(2)\n```')=='print(2)'
    with pytest.raises(FormatError):extract_code('```python\nprint(2)\n```\nHere is more')
    with pytest.raises(SyntaxError):extract_code('Here is the answer: 2')
