# IMPORTS
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import cairo 
import math
import RNA

from datetime import timedelta
from datetime import datetime
import platform
import random
import time
import csv
import re
import os

if platform.system() == 'Windows':
    import winsound

class AptamerForge:
    """
    AptamerForge is an ssDNA aptamer screening tool that allows you to search for Hairpin structures which includes unconventional pairing bases like TT, CT, CC, GG, AA, and AG.
    This aids in the synthesis of ssDNA aptamers rich in unconventional mismatches.

    Usage:
    from aptamerforge import AptamerForge

    #initialize an object
    tt = AptamerForge()

    # Members you can set:
    target_mismatch: a tuple that contains the mismatch you want to search for.
        A tuple that contains target mismatch you are searching for. 
        Example if you want aptamers rich in TT and/or CT, set target_mismatch = ('tt', 'ct'). It is case insensitive.
        If you want to screen for only one mismatch, use set target_mismatch = ('gg',). Don't forget to bring the comma after the mismatch sequence.

    Public Methods:
        -   search(search_space = 1_000_000): how many samples should it search within.
        -   draw_all() : Draws all the candidates found so far into a folder named 'imgs'
        -   draw(seq): allows you to draw the image of a single sequence.
    """

    def __init__(self, target_mismatch = ('tt',), strand_length = 24, filename = '', 
                 min_mismatch_count = 3, min_loop_count = 3, max_dangle_count = 5, min_stem_count = 5, 
                 min_mfe = -13, temperature = 37, author = '', title = '', must_have_all = False, will_plot_hairpin = True):

        # LOCAL VARIABLES.
        self.temperature = temperature
        self.MIN_MFE = min_mfe
        self.target_mismatch = [target.upper() for target in target_mismatch]
        self.time_found = ""
        self.strand_length = strand_length
        self.__sequences___ = set()
        self.MHA = must_have_all
        if will_plot_hairpin and not os.path.exists("imgs"):
            os.makedirs("imgs")
        if filename == '':
            self.fln = f'{"-".join(target_mismatch)}-aptamers.csv'
        else:
            self.fln = filename
        if not self.fln.endswith('.csv'):
            self.fln = f'{self.fln}.csv' 
        if not os.path.exists(self.fln): #Create a new file
            with open(self.fln, mode='w', newline='') as log:
                writer = csv.writer(log)
                writer.writerow(["Sequence", "Sequence Length", "Mismatch Count in Stem", "Stem Count", "Loop Count", "Dangle Count", "Mean Free Energy (kcal/mol)", "Time Found"])
        else: #Open and load sequences.
            with open(self.fln, mode='r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    self.time_found = row['Time Found']
                    self.__sequences___.add(row['Sequence'])
        self.__1counts_so_far1___ = len(self.__sequences___)
        self.min_mismatch_count = min_mismatch_count
        self.min_loop_count = min_loop_count
        self.max_dangle_count = max_dangle_count
        self.min_stem_count = min_stem_count
        
        # DEFINE CORRECT PATTERN SEQUENCE.
        self.fpattern = re.compile(r'^([ATCG])\1{6,}')
        self.bpattern = re.compile(r'([ATCG])\1{6,}$')

        # DEFINE AUTHORS
        self.author = author if author != '' else '© Created by William Asamoah'
        self.title = title if title != '' else f'{", ".join(self.target_mismatch)} Mismatch Search Engine'

        # Notify user of done creation.
        print(f"\033[30m<<Search Engine Initialized on: {', '.join(self.target_mismatch)}, mismatches. | Logging to: {self.fln} ({self.__1counts_so_far1___})| Author: {self.author}>>")

    def __dir__(self):
        return ['search', 'draw', 'draw_all', '__doc__']
    
    def __repr__(self):
        return f"\033[30m<<AptamerForge Search Engine Initialized on: {', '.join(self.target_mismatch)}, mismatches. | Logging to: {self.fln} ({self.__1counts_so_far1___})| Author: {self.author}>>"

    def __str__(self):
        if self.__1counts_so_far1___ == 0:
            return "<No Sequence found so far>"
        str_ = [f"{seq:<30}" + ('\n' if i%4==0 else ' ') for i, seq in enumerate(self.__sequences___)]
        return ''.join(str_)
    
    def __is_normal_seq___(self, seq):
        return (((not self.fpattern.match(seq)) and (not self.bpattern.search(seq))) and (all(base in seq for base in "CTAG")))
    
    def __roll___(self, seq, n=1):
        """
        this rolls the window
        """
        n = n % len(seq)
        seq = seq[n:] + seq[:n]
        return seq
    
    def __get_reversed_seq_i___(self, seq):
        seq_i = [(c, i+1) for i, c in enumerate(seq)]
        seq_i.reverse()
        return seq_i
    
    def __get_mark___(self, a, b):
        #if ((f'{a}{b}' in ('GC', 'CG')) or (f'{a}{b}' in ('AT', 'TA'))):
        #    return '1'
        #else:
        #    if self.MHA:
        #        if 
        if (((a == 'G') and (b == 'C')) or ((b == 'G') and (a == 'C'))):
            return '1'
        elif (((a == 'A') and (b == 'T')) or ((b == 'A') and (a == 'T'))):
            return '1'
        elif (f'{a}{b}' in self.target_mismatch):
            return '0'
        else: 
            return 'x'
    
    def __is_hairpin___(self, seq_idx):
        """
        ✅ Solid Without Containers [Slower] (Loop counting) (nearest index retrieval)
        Returns: stem_counts, loop_counts
        """
        istack = [0]; #lstack=[0]
        last_nz = -1
        prev = -1
        x, y = 0, 0
        loop_count = 0      
        _x, _y = 0, 0

        is_flipped = False
        for i, hp in enumerate(seq_idx):
            # istacking
            if hp > 0:
                istack[-1] += 1
            else:
                istack.append(0)
            while ((len(istack) > 1) and (istack[-1] == 0) and (istack[-2] == istack[-1])):
                istack.pop()
                
            # Loop checking.
            
            if ((last_nz > 0) and ((last_nz - (prev - hp)) == 0)):
                _x = i - 1
            if ((last_nz - (prev - hp)) >= len(seq_idx)):
                _y = i

            loop_count = _y - _x - 1
            if loop_count > 0:
                #lstack[-1] = loop_count
                x, y = _x, _y
            #print(f'{hp:<4}: (last_nz = {last_nz:>4}) (prev - hp = {prev - hp:>4}) (last_nz - (prev - hp) = {last_nz - (prev - hp): <4}) x = {x:<3} y = {y:>3} loop count: {loop_count:<4} lstack: {lstack}');

            #check flip condition
            if ((last_nz < 0) and (hp > 0) and (hp != max(seq_idx))):
                is_flipped = True
            
            if hp > 0:
                last_nz = hp
            prev = hp
        while ((len(istack) > 1) and (istack[-1] == 0)):
            istack.pop()
        #print(istack)
        loop_count = y - x - 1
        is_loop_more_than_stem = loop_count > istack[0]
        return (
            ((len(istack) == 2) and (istack[-1] == istack[-2]) and (istack[0] >= self.min_stem_count) and (loop_count >= self.min_loop_count) and (not is_flipped) and (not is_loop_more_than_stem)), 
            istack[0], loop_count
            )
    
    def __ptable___(self, seq):
        # Keep the original structure
        # Keep rolling the reversed structure till you get more stems matching
        seq_ = list(seq)
        rseq_i = self.__get_reversed_seq_i___(seq)
        counts = 0

        while (counts <= (len(seq) ** 2)):
            for i in range(len(seq_)):
                ptbl = [(k, i[0], i[1], self.__get_mark___(k, i[0]), i[1] if self.__get_mark___(k, i[0]) != 'x' else 0) for k, i in zip(seq_, rseq_i)]
                t_df = pd.DataFrame(ptbl, columns=('Original', 'Rolled', 'Index', 'Pairing', 'Seq Indices'))
                
                # Get a list of the Seq Indices.
                seq_idx = list(t_df['Seq Indices'])

                # if loop is 2, make neighbours 0 since they will not pair.
                # loop counts
                prev = -1
                last_nz = -1
                x, y = 0, 0
                _x, _y = 0, 0
                
                for i, hp in enumerate(seq_idx):
                    if ((last_nz > 0) and ((last_nz - (prev - hp)) == 0)):
                        _x = i - 1
                    if ((last_nz - (prev - hp)) >= len(seq_idx)):
                        _y = i
                    if hp > 0:
                        last_nz = hp
                    prev = hp
                    loop_count = _y - _x - 1
                    if loop_count > 0:
                        x, y = _x, _y
                if ((y - x) == 3):
                    seq_idx[y] = 0
                    seq_idx[x] = 0
                    #print(f'Correcting 2 motif loop at: i = {x} and j = {y}. seq_idx = {seq_idx}')
                    t_df['Seq Indices'] = seq_idx
                    #display(t_df)
                
                # Check hairpin
                isHairpin, stem_count, loop_count = self.__is_hairpin___(seq_idx)
                #print(f'count: {counts} isHairpin: {isHairpin} seq_idx = {seq_idx}')
                #print(f'{isHairpin}, stem: {stem_count}, loop: {loop_count}')
                if isHairpin:
                    return (t_df, stem_count, loop_count)
                
                rseq_i = self.__roll___(rseq_i)
                counts += 1
        
            seq_ = self.__roll___(seq_)
        return (None, 0, 0)
    
    def __count_mismatches___(self, seq):
        # Count TT in Stem not in Loop.
        pt_df, stem_count, loop_count = self.__ptable___(seq)
        #print(f"<count_tt_mismatch> pt_df = {pt_df} stem = {stem_count} loop={loop_count}")
        mismatch_count = 0
        if pt_df is not None:
            mismatch_count = (pt_df[pt_df['Seq Indices'] != 0]['Pairing'] == '0').sum()//2
        return (mismatch_count, stem_count, loop_count)

    def __has_mismatches___(self, seq):
        mismatch_count, stem_count, loop_count = self.__count_mismatches___(seq)
        return ((mismatch_count >= self.min_mismatch_count), mismatch_count, stem_count, loop_count)

    @staticmethod
    def __beepiq___():
        system = platform.system()

        if system == "Windows":
            winsound.Beep(477, 133)
        elif system == 'Darwin':
            os.system('afplay /System/Library/Sounds/Funk.aiff')
        elif system == 'Linux':
            if os.system('command -v beep >/dev/null 2>&1') == 0:
                os.system('beep')
            else: 
                print('\a')

    def __get_MFE___(self, seq):
        md = RNA.md()
        md.temperature = self.temperature
        md.dna = True
        fc = RNA.fold_compound(seq, md)

        _, mfe = fc.mfe()

        return mfe
    
    def search(self, search_space = 1_000_000):
        """
        Generate strand
        If strand is normal DNA seq and has desired MFE, check if it has required number of desired mismatches.
        Then log: <seq>, <tt-mismatch count>, <mfe>
        """

        no_checked = 0

        start = time.time()
        for i in range(search_space+1):
            seq = ''.join(random.choices(['A', 'C', 'T', 'G'], k=self.strand_length))
            mfe = self.__get_MFE___(seq)
            if ((not self.__is_normal_seq___(seq)) and (mfe > self.MIN_MFE) and (seq in self.__sequences___)):
                continue

            no_checked += 1
            
            # is mismatch candidate?
            if (mfe <= self.MIN_MFE): 
                isMismatch, mismatch_counts, stem_cc, loop_cc = self.__has_mismatches___(seq)

                if (isMismatch):
                    self.__1counts_so_far1___ += 1
                    dangle_cc = self.strand_length - loop_cc - 2*stem_cc
                    self.__beepiq___()
                    time_found = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.__sequences___.add(seq)
                    
                    with open(self.fln, mode="a", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow([seq, self.strand_length, mismatch_counts, stem_cc, loop_cc, dangle_cc, f"{mfe:.2f}", time_found])

            #Update to the user
            fmt_time = str(timedelta(seconds=int(time.time() - start)))
            
            print(f"Seq: \033[1;35m{seq} | \033[1;31mElapsed Time: \033[36m{fmt_time} \033[1;32mFound \033[4;34m{self.__1counts_so_far1___:,}\033[0;37m ({time_found})\033[0m in \033[33m{no_checked:,}/{search_space:,}", end="\r")

    def __get_helper_fields___(self, seq):
        # Get PTABLE
        df_, stem_cc, loop_cc = self.__ptable___(seq); 
        if df_ is None:
            return (None, None, None, None, None, None, None)
        bases = list(seq)
        seq_idx = df_['Seq Indices'].values.tolist()
        pairing_x = df_['Pairing'].values.tolist()

        # Containers.
        prev_hp = []; loop_ccs = [];

        # Auxiliary Aiders
        istack = [0]
        last_nz = -1; prev = -1
        loop_count = 0
        _x, _y = 0, 0
        
        for i, hp in enumerate(seq_idx):
            # istacking
            if hp > 0:
                istack[-1] += 1
            else:
                istack.append(0)
            while ((len(istack) > 1) and (istack[-1] == 0) and (istack[-2] == istack[-1])):
                istack.pop()
                
            # Loop checking.
            if ((last_nz > 0) and ((last_nz - (prev - hp)) == 0)):
                _x = i - 1
            if ((last_nz - (prev - hp)) >= len(seq_idx)):
                _y = i
            loop_count = _y - _x - 1
            prev_hp.append(prev - hp); loop_ccs.append(loop_count)
            if hp > 0:
                last_nz = hp
            prev = hp
            
        while ((len(istack) > 1) and (istack[-1] == 0)):
            istack.pop()
            
        return (bases, seq_idx, pairing_x, loop_ccs, prev_hp, stem_cc, loop_cc)

    def __dr4w___(self, seq, wid___th, hei___ght, font_size = 54, w = 203, margin = 50):
        bases, seq_idx, pairing_x, loop_ccs, prev_hp, stem_count, loop_count = self.__get_helper_fields___(seq)
        if (not hasattr(bases, '__len__')) or (len(bases) == 0):
            print("Sequence not a hairpin")
            return
        drawing_limit_y = hei___ght - 250  # prevent overlap with footer

        #1 Draw the backbone first
        cx, cy = wid___th//2, hei___ght//2
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, wid___th, hei___ght)
        ctx = cairo.Context(surface)

        # Background
        ctx.set_source_rgb(0.98, 0.98, 0.98)  # light gray
        ctx.rectangle(0, 0, wid___th, hei___ght)
        ctx.fill()

        # === Title ===
        ctx.set_font_size(120)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_source_rgb(0.1, 0.1, 0.1)
        ctx.move_to(33, 170)
        ctx.show_text(self.title)
        ctx.set_source_rgb(0.3, 0.3, 0.3)
        ctx.set_line_width(5)
        ctx.set_dash([])
        ctx.move_to(33, 220)
        ctx.line_to(wid___th - 33, 220)
        ctx.stroke()

        # === Sequence Details ===
        # Name.
        ctx.set_font_size(45)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_source_rgb(0.3, 0.3, 0.3)
        ctx.move_to(33, 290)
        ctx.show_text("Sequence: ")
        ctx.set_font_size(45)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_source_rgb(0.3, 0.3, 0.9)
        ctx.move_to(260, 290)
        ctx.show_text(f"{seq}")
        # Stem Count.
        ctx.set_font_size(45)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_source_rgb(0.3, 0.3, 0.3)
        ctx.move_to(wid___th - 1333, 290)
        ctx.show_text("Stem Count: ")
        ctx.set_font_size(45)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_source_rgb(0.3, 0.3, 0.9)
        ctx.move_to(wid___th - 1063, 290)
        ctx.show_text(f"{stem_count}")
        # Loop Count.
        ctx.set_font_size(45)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_source_rgb(0.3, 0.3, 0.3)
        ctx.move_to(wid___th - 933, 290)
        ctx.show_text("Loop Count: ")
        ctx.set_font_size(45)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_source_rgb(0.3, 0.3, 0.9)
        ctx.move_to(wid___th - 673, 290)
        ctx.show_text(f"{loop_count}")
        # MFE.
        ctx.set_font_size(45)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_source_rgb(0.3, 0.3, 0.3)
        ctx.move_to(wid___th - 493, 290)
        ctx.show_text("MFE: ")
        ctx.set_font_size(45)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_source_rgb(0.3, 0.3, 0.9)
        ctx.move_to(wid___th - 333, 290)
        mfe = self.__get_MFE___(seq)
        if mfe > -5:
            ctx.set_source_rgb(0.9, 0.3, 0.1)
        else:
            ctx.set_source_rgb(0.1, 0.3, 0.9)
        ctx.show_text(f"{mfe:.2f} kcal/mol")

        # === Legend ===
        ctx.set_font_size(43)
        legend_x, legend_y = 0.83*wid___th, 0.33*hei___ght

        # Canonical
        ctx.set_source_rgb(0, 0, 0)
        ctx.set_line_width(3)
        ctx.set_dash([])
        ctx.move_to(legend_x, legend_y)
        ctx.line_to(legend_x + 70, legend_y)
        ctx.stroke()
        ctx.move_to(legend_x + 80, legend_y + 5)
        ctx.show_text("Canonical Pair")

        # T–Hg²⁺–T
        ctx.set_source_rgb(1, 0, 0)
        ctx.set_dash([5.0, 2.0])
        ctx.move_to(legend_x, legend_y + 40)
        ctx.line_to(legend_x + 70, legend_y + 40)
        ctx.stroke()
        ctx.set_dash([])
        ctx.set_source_rgb(0, 0, 0)
        ctx.move_to(legend_x + 80, legend_y + 45)
        ctx.show_text(f"{', '.join(self.target_mismatch)}")


        # === Hair Pin Shape ===
        ctx.set_source_rgb(0.98, 0.98, 0.98)  # light gray
        points = []
        sx, sy = 0.001*wid___th, 0.897*hei___ght
        #points.append((sx, sy))
        len_t = len(bases); lpstack = []; lpstack.append(loop_ccs[0])
        angle = (2*math.pi)/(loop_count + 2); 
        start_angle = -((3*math.pi - angle)/2) # -(math.pi + angle)
        theta = start_angle
        r = (w/2) / math.sin(angle/2) # (w/2) / math.cos(angle)
        t_x, t_y = 0, 0
        cx, cy = 0, 0
        for i in range(len_t):
            if loop_ccs[i] != lpstack[-1]:
                lpstack.append(loop_ccs[i])
            if len(lpstack) == 1: # This is 5' danglings and stem.
                t_x, t_y = points[-1] if len(points) != 0 else (sx, sy)
                if t_y > drawing_limit_y:
                    t_y = drawing_limit_y
                if prev_hp[i] <= 0:
                    points.append((t_x + w, t_y))
                else:
                    points.append((t_x, t_y - w))
            elif (len(lpstack) == 2): # We have entered the loop.
                theta += angle
                if prev_hp[i] > 0: # Entry point discovered
                    t_x, t_y = points[-1]
                    if t_y > drawing_limit_y:
                        t_y = drawing_limit_y
                    c_x, c_y = t_x + (w/2), t_y - (w/2)/math.tan(angle/2) #t_x + (w/2), t_y - (w/2)/math.tan(angle)
                    points.append((c_x + r * math.cos(theta), c_y + r * math.sin(theta)))
                else:
                    points.append((c_x + r * math.cos(theta), c_y + r * math.sin(theta)))
            elif (len(lpstack) == 3): # We have entered the stem of 3'
                if prev_hp[i] < 0: # First node.
                    t_x, t_y = points[i - loop_count - 1]
                    if t_y > drawing_limit_y:
                        t_y = drawing_limit_y
                    points.append((t_x + w, t_y))
                else:
                    t_x, t_y = points[-1]
                    if t_y > drawing_limit_y:
                        t_y = drawing_limit_y
                    points.append((t_x, t_y + w))
            elif (len(lpstack) == 4): # We have entered dangle of 5'
                t_x, t_y = points[-1]
                if t_y > drawing_limit_y:
                    t_y = drawing_limit_y
                points.append((t_x + w, t_y))
                
            #print(f'{i}: {points[i]}')
        ctx.fill()

        # Plot the Structure
        ctx.set_source_rgb(0.0, 0.7, 1.0)
        ctx.set_line_width(3)
        ctx.move_to(sx, sy)
        for point in points:
            _x, _y = point
            ctx.line_to(_x, _y)
        ctx.stroke()

        # Draw the links
        # x x x x x 0 1 0 1 0 1 1 1 x x 1 1 1 0 1 0 1 0 x x
        drawn = [False] * len_t
        for i, s_idx in enumerate(seq_idx):
            #print(pairing_x[i], end=' ')
            if s_idx == 0:
                continue
            elif s_idx != 0:
                t_x, t_y = points[i]
                to_x, to_y = points[s_idx-1]
                
                if pairing_x[i] == '1': # cannonical pair
                    ctx.set_source_rgb(0, 0, 0)
                    ctx.set_dash([])
                    
                elif pairing_x[i] == '0': # T - T mismatch
                    ctx.set_source_rgb(1, 0, 0)
                    ctx.set_dash([5.0, 2.0])

                if not drawn[s_idx - 1]:
                    ctx.set_line_width(2)
                    ctx.move_to(t_x, t_y)
                    ctx.line_to(to_x, to_y)
                    ctx.stroke()
                drawn[i] = True
        
        # Annotate
        for i, (x, y) in enumerate(points):
            base = bases[i]
            
            #Circle
            ctx.arc(x, y, 43, 0, 2 * math.pi)
            ctx.set_source_rgb(0.98, 0.98, 0.98)
            ctx.fill_preserve()
            ctx.set_source_rgb( 0, 0, 0)
            ctx.set_line_width(0)
            ctx.stroke()
            
            #Base letter
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(font_size)
            #xbearing, ybearing, width, height, _, _ = ctx.text_extents(base)
            ctx.move_to(x - font_size/2 + 7, y + font_size/2 - 3) #ctx.move_to(x - width / 2 - xbearing, y + height / 2)
            if pairing_x[i] == '0':
                ctx.set_source_rgb(1, 0, 0)
            else:
                ctx.set_source_rgb(0, 0.56, 1)
            ctx.show_text(base)
        ctx.stroke()
                    

        # === Footer Branding ===
        ctx.set_source_rgb(0.7, 0.7, 0.67)
        ctx.set_line_width(7)
        ctx.set_dash([])
        ctx.move_to(33, hei___ght - 170)
        ctx.line_to(wid___th - 33, hei___ght - 170)
        ctx.stroke()
        ctx.set_font_size(57)
        ctx.set_source_rgb(0.43, 0.57, 0.53)
        ctx.move_to(33, hei___ght - 100)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.show_text(f"{self.author} • Mismatch Aptamer Engine v1")
        ctx.set_font_size(47)
        ctx.set_source_rgb(0.3, 0.4, 0.6)
        ctx.move_to(33, hei___ght - 50)
        ctx.show_text("© William Asamoah | cephaswills@gmail.com | www.linkedin.com/in/eicheiel | www.github.com/Feicheiel")

        # === Save Image ===
        surface.write_to_png(f"imgs/{seq}.png")
        print(f"✅ Image saved: {seq}.png")

    def draw_all(self, width = 3000, height = 2700):
        for seq in self.__sequences___:
            self.__dr4w___(seq, wid___th = width, hei___ght = height)
    
    def draw(self, seq, width = 3000, height = 2700):
        self.__dr4w___(seq, wid___th = width, hei___ght = height)
