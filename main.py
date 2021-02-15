# -*- coding: utf-8 -*-

"""-------------------------------------------------------------------------+++
Script main.
"""

# embedded in python
import os
# pip install
import pandas as pd
from numpy import int
# same folder

def chop( text, L, R ):
    """Chops the text str as instructed."""
    A, B = 0, len(text) # это соотв. iloc, изменится в будущем
    
    #если присутствует L
    if type(L)==int: A = L
    elif type(L)==str or type(L)==bytes: A = text.find(L)+len(L)
    text = text[A:]
    
    #если присутствует R
    if type(R)==int: B = R
    elif type(R)==str or type(R)==bytes: B = [B,text.find(R)][R in text]
    
    return text[:B].strip()

def readf( path, enc='utf-8' ):
    with open( path, 'r', encoding=enc ) as f:
        return f.read()
    
def savef( path, text ):
    with open( path, 'w', encoding='utf-8' ) as f:
        f.write(text)
    
def appef( path, text ):
    with open( path, 'a', encoding='utf-8' ) as f:
        f.write(text)

class shablon( object ):
    
    # maximim amount of phonemes that human should pronounce in one breath
    MAX_PHONEMES = 7
    
    def __init__( self,
                  *args, **kwargs ):
        super( __class__, self ).__init__( *args, **kwargs )
        
        # get all necessary info from research.xls
        self.dfs = self._getdfs()
        
    """---------------------------------------------------------------------+++
    Everything about i/o.
    """
    @staticmethod
    def _getdfs():
        # get source df
        src = pd.read_excel( 'research.xls' )
        
        # find splits
        spans = []
        for iloc, col in enumerate(src.columns):
            if col.count('↓')==2: spans.append(iloc)
            
        # split it
        dfs = {}
        for L,R in zip(spans[:-1],spans[1:]):
            cols = src.columns[L+1:R]
            df = src[ cols ]
            dfs.setdefault( src.columns[L], df )
        
        return dfs
    
    """---------------------------------------------------------------------+++
    Everything about connecting.
    """
    def stupid_connect( self ):
        # primitive letter connecting
        # saves all letter combinations to text files
        """-----------------------------------------------------------------+++
        Definitions.
        """
        GLUE = self.dfs['↓glue↓'] # df i'm working with
        DATA = self.dfs['↓data↓'] # short name for df with data
        
        # remove dots from ununique src columns
        GLUE.columns = [ chop(c,None,'.') for c in GLUE.columns ]
        DATA.columns = [ chop(c,None,'.') for c in DATA.columns ]
        
        def matching( desciloc ):
            """Selects letters, that match ↓description."""
            cols = GLUErow['%s data'%desciloc].split(' ')
            pool = '%s pool'%desciloc
            
            # select from data according to columns and pool
            # generate masks
            masks = []
            for col in cols: masks.append( DATA[col]==1 )
            masks.append( DATA['pool']==GLUErow[pool] )
            mask = masks[0]
            # combine masks
            if len(masks)>1:
                for m in masks[1:]: mask=mask&m
            # select
            sub = DATA[ mask ]
            
            return sub
        
        def iterdescriptions( L, stacks, stack ):
            # i don't know how many columns there are
            # see current letter description №L
            for desciloc in range( L, len(GLUE.columns) ):                
                # there are no more letter descriptions
                col = '%s data'%desciloc
                if (not col in GLUE.columns) or pd.isna(GLUErow[col]):
                    # there are still some letters to process
                    # on previous levels
                    if L>1:
                        stacks.append([])
                        return None
                    # there are no letters to process anymore
                    else:
                        stacks=stacks[:-1]
                        return None
                
                # add all matching letters to stack
                ltrs = matching(desciloc)
                for ltrloc, ltrrow in ltrs.iterrows():
                    # add letter to the last stack
                    text = ltrrow['iloc'] # 'sound' for preview
                    stacks[-1] = stack+[text]
                        
                    # see next desc
                    iterdescriptions( desciloc+1, stacks, stacks[-1] )
                return None #if L==1: return None
        
        """-----------------------------------------------------------------+++
        Actual code.
        """
        # iterate through GLUE (DATA combining rules)
        for GLUEloc, GLUErow in GLUE.iterrows():
            # skip
            if pd.isna(GLUErow['pack']): continue # this row is empty
            if not GLUErow['rec']==1: continue # don't want to use this rule
        
            PACKNAME = GLUErow['pack']
            
            # iterate through all letter descriptions from №1 to ?????
            # and get all letter combinations
            STACKS = [ [], ] # destination for letter combinations
            iterdescriptions( 1, STACKS, [] )
            
            # save to file
            texts = []
            for stack in STACKS: texts.append( ' '.join([ str(s) for s in stack]) )
            appef( 'stupid_%s.txt'%(PACKNAME), '\n\n' )
            appef( 'stupid_%s.txt'%(PACKNAME), '\n'.join(texts) )
    
    def compress_stupidconnections( self ):
        """-----------------------------------------------------------------+++
        Definitions.
        """
        def remove_double_sounds( path ):
            # removes "бба" from CCV
            lines = readf(path).split('\n')
            
            lineiloc = 0
            while lineiloc<len(lines):
                split = lines[lineiloc].split(' ')
                # this line is not applicable
                if len(split)<3:
                    lineiloc+=1
                    continue
                
                if split[0]==split[1]: lines.pop(lineiloc)
                else: lineiloc+=1
            
            savef( path, '\n'.join(lines) )
            
        def embed_cv_into_ccv( cvpath, ccvpath ):
            # embeds "ва" into "бва"
            cvlines = readf(cvpath).split('\n')
            ccvtext = readf(ccvpath)
            
            cvlineiloc = 0
            while cvlineiloc<len(cvlines):
                cvline = cvlines[cvlineiloc]
                # this line is not applicable
                if len(cvline)==0:
                    cvlineiloc+=1
                    continue
                
                if cvline in ccvtext: cvlines.pop(cvlineiloc)
                else: cvlineiloc+=1
                
            savef( cvpath, '\n'.join(cvlines) )
            
        def loop_lines( path ):
            lines = readf(path).split('\n')

            # remove empty lines
            lineiloc = 0            
            while lineiloc<len(lines):
                if len(lines[lineiloc])<1: lines.pop(lineiloc)
                else:
                    lineiloc+=1
                    continue
                
            savef( path, ' '.join(lines) )
            
        def compress_triple_sounds( path ):
            # converts "аааыуэо" into "ааыуэо"
            ltrs = readf(path).split(' ')
            
            ltriloc = 0
            while ltriloc<len(ltrs)-2:
                ltr = ltrs[ltriloc]
                # this letter is not applicable
                if len(ltr)<1:
                    ltriloc+=1
                    continue
                
                nextltr1 = ltrs[ltriloc+1]
                nextltr2 = ltrs[ltriloc+2]
                
                if ltr==nextltr1==nextltr2: ltrs.pop(ltriloc)
                else: ltriloc+=1
            
            savef( path, ' '.join(ltrs) )
            
        def compress_vc_into_loop( vcpath, loopath ):
            # embeds "ав" into "бва вде"
            vclines = readf(vcpath).split('\n')
            lootext = readf(loopath)
            
            vclineiloc = 0
            while vclineiloc<len(vclines):
                vcline = vclines[vclineiloc]
                # this line is not applicable
                if len(vcline)==0:
                    vclineiloc+=1
                    continue
                
                if vcline in lootext: vclines.pop(vclineiloc)
                else: vclineiloc+=1
                
            savef( vcpath, '\n'.join(vclines) )
        
        """-----------------------------------------------------------------+++
        Actual code.
        """
        # get stupid_connect output
        packs = {}
        for f in os.listdir():
            name, ext = os.path.splitext(f)
            # skip other files
            if not ext=='.txt': continue
            if not 'stupid_' in name[:len('stupid_')]: continue
            PACKNAME = chop(name,'stupid_',None)
            packs.setdefault( PACKNAME, f )
            
        # compress doubles in CCV
        if 'CCV' in packs: remove_double_sounds( packs['CCV'] )
        if 'CCVb' in packs: remove_double_sounds( packs['CCVb'] )
        # compress CV into CCV
        if 'CV' in packs and 'CCV' in packs:
            embed_cv_into_ccv( packs['CV'], packs['CCV'] )
        if 'CVb' in packs and 'CCVb' in packs:
            embed_cv_into_ccv( packs['CVb'], packs['CCVb'] )
            
        # loop some lines
        if 'CV' in packs: loop_lines( packs['CV'] )
        if 'CVb' in packs: loop_lines( packs['CVb'] )
        if 'CCV' in packs: loop_lines( packs['CCV'] )
        if 'CCVb' in packs: loop_lines( packs['CCVb'] )
        if 'CyV' in packs: loop_lines( packs['CyV'] )
        if 'CyVb' in packs: loop_lines( packs['CyVb'] )
        if 'VV' in packs: loop_lines( packs['VV'] )
        if 'VVb' in packs: loop_lines( packs['VVb'] )
        
        # compress VV loops
        if 'VV' in packs: compress_triple_sounds( packs['VV'] )
        
        # compress VC into looped something
        if 'VC' in packs and 'CCV' in packs:
            compress_vc_into_loop( packs['VC'], packs['CCV'] )
        if 'VCb' in packs and 'CCVb' in packs:
            compress_vc_into_loop( packs['VCb'], packs['CCVb'] )
        if 'VC' in packs and 'CyV' in packs:
            compress_vc_into_loop( packs['VC'], packs['CyV'] )
        if 'VCb' in packs and 'CyVb' in packs:
            compress_vc_into_loop( packs['VCb'], packs['CyVb'] )
    
    def humanize_stupidcompressions( self ):
        """-----------------------------------------------------------------+++
        Definitions.
        """
        def remove_emptylines( path ):
            # removes empty lines from a file
            lines = readf(path).split('\n')
            
            lineiloc = 0
            while lineiloc<len(lines):
                line = lines[lineiloc]
                if len(line)==0: lines.pop(lineiloc)
                else:
                    lineiloc+=1
                    continue
                
            savef( path, '\n'.join(lines).strip() )
            
        def humanize_loops( path, STEP ):
            ltrs = readf(path).split(' ')
            
            # borders
            MAX_FILL = int(STEP*self.MAX_PHONEMES)
            
            iloc = 0
            lines = []
            line = []
            while iloc<len(ltrs):
                # add letter to line
                ltr = ltrs[iloc]
                line.append( ltr )
                # line is filled
                residue = len(ltrs)%STEP
                if len(line)==MAX_FILL or iloc>=len(ltrs)-residue:
                    #print( len(ltrs), len(ltrs)%STEP )
                    lines.append( ' '.join(line) )
                    line = []
                    
                    # i broke a looping phoneme.
                    # which one?
                
                    # ↓ there is no next letter, end of the cycle
                    if iloc==len(ltrs)-1: break
                
                    # add missing phoneme to ltrs
                    prev_ltrs = ltrs[(iloc+1)-(STEP-1):iloc+1]
                    for pl in prev_ltrs[::-1]:
                        ltrs.insert( iloc+1, pl )
                    
                iloc += 1
                
            savef( path, '\n'.join(lines) )
            
        def merge_c_with_v( cpath, vpath ):
            # embeds "-а" into "・б"
            vlines = readf(vpath).split('\n')
            clines = readf(cpath).split('\n')
            
            vloc = 0
            for cloc in range( len(clines) ):
                # this space in clines is not vacant
                if not clines[cloc][:4]=='1060': continue
                # all vlines are pasted
                if vloc==len(vlines): break
            
                # fit vline here
                clines[cloc] = vlines[vloc]+clines[cloc][4:]
                vloc+=1
            vlines = vlines[vloc:]
            mlines = clines[:vloc]
            clines = clines[vloc:]
                
            savef( cpath, '\n'.join(clines) )
            savef( vpath, '\n'.join(vlines) )
            savef( 'stupid_C+V.txt', '\n'.join(mlines) )
        
        """-----------------------------------------------------------------+++
        Actual code.
        """
        # get stupid_connect output
        packs = {}
        for f in os.listdir():
            name, ext = os.path.splitext(f)
            # skip other files
            if not ext=='.txt': continue
            if not 'stupid_' in name[:len('stupid_')]: continue
            PACKNAME = chop(name,'stupid_',None)
            packs.setdefault( PACKNAME, f )
            
        # remove empty lines
        for k in packs: remove_emptylines(packs[k])
        
        # humanize unpronouncable loops
        if 'CV' in packs: humanize_loops( packs['CV'], 2 )
        if 'CVb' in packs: humanize_loops( packs['CVb'], 2 )
        if 'CCV' in packs: humanize_loops( packs['CCV'], 3 )
        if 'CCVb' in packs: humanize_loops( packs['CCVb'], 3 )
        if 'CyV' in packs: humanize_loops( packs['CyV'], 3 )
        if 'CyVb' in packs: humanize_loops( packs['CyVb'], 3 )
        if 'VV' in packs: humanize_loops( packs['VV'], 2 )
        if 'VVb' in packs: humanize_loops( packs['VVb'], 2 )
        
        # merge C with V
        if 'C' in packs and 'V' in packs:
            merge_c_with_v( packs['C'],packs['V'] )
            
    def render_reclist( self ):
        """-----------------------------------------------------------------+++
        Definitions.
        """
        # get data and remove dots from ununique src columns
        DATA = self.dfs['↓data↓'] # short name for df with data
        DATA.columns = [ chop(c,None,'.') for c in DATA.columns ]
        
        def find_replacement( iloc, col ):
            mask = DATA['iloc']==int(iloc)
            row = DATA[mask].iloc[0]
            text = row[col]
            if pd.isna(text): text=iloc
            return text
        
        def render_text( path, labels ):
            lines = readf(path).split('\n')
            for lineiloc, line in enumerate(lines):
                ltrs = line.split(' ')
                texts = []
                
                labloc = 0
                for ltrloc, ltr in enumerate(ltrs):
                    col = labels[labloc]
                    labloc+=1
                    if labloc==len(labels): labloc=0
                    texts.append( find_replacement(ltr,col) )
                lines[lineiloc] = '\t'.join(texts)
                
            savef( path, '\n'.join(lines) )
            
        def render_single( path ):
            # removes empty lines from a file
            lines = readf(path).split('\n')
            
            lineiloc = 0
            while lineiloc<len(lines):
                line = lines[lineiloc]
                if len(line)==0: lines.pop(lineiloc)
                else:
                    lineiloc+=1
                    continue
                
            appef( 'reclist.txt', '\n'+'\n'.join(lines).strip() )
        
        """-----------------------------------------------------------------+++
        Actual code.
        """
        # get stupid_connect output
        packs = {}
        for f in os.listdir():
            name, ext = os.path.splitext(f)
            # skip other files
            if not ext=='.txt': continue
            if not 'stupid_' in name[:len('stupid_')]: continue
            PACKNAME = chop(name,'stupid_',None)
            packs.setdefault( PACKNAME, f )
        
        if 'CV' in packs:
            render_text( packs['CV'], ['sym main','sym main'] )
        if 'CVb' in packs:
            render_text( packs['CVb'], ['sym main','sym main'] )
        if 'C' in packs:
            render_text( packs['C'], ['sym solo','sym solo'] )
        if 'VC' in packs:
            render_text( packs['VC'], ['sym solo','sym solo'] )
        if 'VCb' in packs:
            render_text( packs['VCb'], ['sym solo','sym solo'] )
        if 'VV' in packs:
            render_text( packs['VV'], ['sym main','sym main'] )
        if 'VVb' in packs:
            render_text( packs['VVb'], ['sym main','sym main'] )
        if 'CCV' in packs:
            render_text( packs['CCV'], ['sym solo','sym main','sym main'] )
        if 'CCVb' in packs:
            render_text( packs['CCVb'], ['sym solo','sym main','sym main'] )
        if 'CyV' in packs:
            render_text( packs['CyV'], ['sym solo','sym solo','sym main'] )
        if 'CyVb' in packs:
            render_text( packs['CyVb'], ['sym solo','sym solo','sym main'] )
        if 'C+V' in packs:
            render_text( packs['C+V'], ['sym main','sym main','sym solo'] )
            
        for k in packs: render_single(packs[k])
        
"""-------------------------------------------------------------------------+++
autorun
"""
def autorun():
    ob = shablon()
    ob.stupid_connect()
    ob.compress_stupidconnections()
    ob.humanize_stupidcompressions()
    ob.render_reclist()

if __name__ == '__main__':
    autorun()
    
#---------------------------------------------------------------------------+++
# конец 2021.02.15 → 2021.02.15
