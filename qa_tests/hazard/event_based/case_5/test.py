# Copyright (c) 2010-2014, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os

import numpy

from nose.plugins.attrib import attr
from openquake.engine.db import models
from qa_tests import _utils as qa_utils

GET_GMF_OUTPUTS = '''
select gsim_lt_path, array_concat(gmvs order by site_id, task_no) as gmf
from hzrdr.gmf_data as a, hzrdr.lt_realization as b, hzrdr.gmf as c
where lt_realization_id=b.id and a.gmf_id=c.id and c.output_id in
(select id from uiapi.output where oq_job_id=%d and output_type='gmf')
group by gsim_lt_path, c.output_id, imt, sa_period, sa_damping
order by c.output_id;
'''

# this is an example with 0 realization for source_model 1
# 5 realizations for source model 2
# (for TRT=Stable Shallow Crust) and 0 realizations
# for source model 3, i.e. a total of 5 realizations
EXPECTED_GMFS = [
    # (gsim_lt_path, gmf) pairs
    (['b2_1'],
     [0.00562957229517, 0.0131253865659, 0.0175321501225, 0.00362202386023,
      0.00527202329311, 0.00572769346224, 0.00506188168111, 0.0312416289461,
      0.0501701034411, 0.0333257666386, 0.0062124013171, 0.352152345105,
      0.072546276031, 0.0403383374284, 0.00510886303682, 0.0202439766433,
      0.00980952578658, 0.0171027621698, 0.0221131045931, 0.0163468283692,
      0.0528919955473, 0.0038381044707, 0.00871974934378, 0.00549022692682,
      0.00536720077375, 0.0097925777452, 0.0207659431635, 0.0152122000845,
      0.00527501941576, 0.0147942195355, 0.00535695376225, 0.0166089652316,
      0.00622087307454, 0.061290472162, 0.00676213774025, 0.0142723280034,
      0.0275752455752, 0.0654099108868, 0.0961796070347, 0.0398997926388,
      0.0370751276227, 0.00916732318106, 0.00513742610917, 0.0297793365632,
      0.0892922182646, 0.00549486552929, 0.0397647760742, 0.0331365025278,
      0.00162018158379, 0.0130474276583, 0.00268199765415, 0.0104156739837]),
    (['b2_2'],
     [0.00252084451095, 0.00864925448207, 0.0124358526944, 0.00159758009804,
      0.00257580487464, 0.00216061096866, 0.00180628864111, 0.0184407039105,
      0.0310937547639, 0.0184963514803, 0.00241283208231, 0.261700841865,
      0.0464526529838, 0.0171502176804, 0.00215005801291, 0.00753960188298,
      0.00520619474794, 0.00958245553051, 0.00983449955032, 0.0100744812609,
      0.0192526977825, 0.001353962746, 0.00468411850433, 0.00121109430049,
      0.00205017539981, 0.00540166393365, 0.00871153400718, 0.00467232984253,
      0.00192636762393, 0.00504452583706, 0.00215645012671, 0.005526706105,
      0.00242187621667, 0.0265124245253, 0.00154500530213, 0.00625961538488,
      0.00723646472094, 0.0260510279498, 0.0435471801018, 0.0144797058956,
      0.0179813370631, 0.00278004438492, 0.00197381057504, 0.010885080571,
      0.0194544941145, 0.00129255295019, 0.0165478520702, 0.00900676207328,
      0.000501196538144, 0.00681599248841, 0.000560393030523,
      0.00359708596215]),
    (['b2_3'],
     [0.00551290378335, 0.011223071495, 0.0150119190645, 0.00330498975319,
      0.00483873723178, 0.00674465810018, 0.00597389121748, 0.033146720118,
      0.0534285326719, 0.0358934922076, 0.00668754848657, 0.332698182623,
      0.0749563591433, 0.0462842877229, 0.00523319424412, 0.0243349406971,
      0.00848415648128, 0.0177283976511, 0.0238637957719, 0.0159937867834,
      0.0693961993972, 0.00369268772438, 0.00845455833741, 0.00725639293515,
      0.00514706366357, 0.00960529035875, 0.0231356349195, 0.0192776155095,
      0.00510960132902, 0.0178179180287, 0.00495121861389, 0.0205333711191,
      0.00595376712967, 0.0702743826793, 0.0089939443523, 0.0140104866787,
      0.03463762244, 0.0851417454644, 0.095504017347, 0.0515862031989,
      0.0372149960067, 0.0110678848562, 0.00484110216473, 0.0379107750369,
      0.0786723205971, 0.00719929367659, 0.0409099092544, 0.0414138885234,
      0.00145427952201, 0.0118700709242, 0.00311192464915, 0.0109411002004]),
    (['b2_4'],
     [0.00748909249818, 0.0203907495897, 0.0278599676385, 0.00490986010101,
      0.00733647937863, 0.0055852752736, 0.00486731140451, 0.0388977223761,
      0.0639563625296, 0.0409688654964, 0.00646528247662, 0.540545748059,
      0.0980896427301, 0.0426858222201, 0.00722445166909, 0.0195099327032,
      0.0148639729211, 0.0250673580569, 0.0232323977689, 0.0255707167495,
      0.0449815592133, 0.00509226218204, 0.013262124452, 0.00445530846823,
      0.007227045778, 0.0148693709255, 0.0213511683527, 0.0135671388831,
      0.00701290622212, 0.0140253767625, 0.00749682476066, 0.0153614775656,
      0.00843590166816, 0.0590808192058, 0.005467367583, 0.0190344613396,
      0.0212575556307, 0.0567265826524, 0.114080574086, 0.0352059833648,
      0.047405877272, 0.00847033277556, 0.0070432742881, 0.0268929609785,
      0.0779302186289, 0.00451651015653, 0.0458021067747, 0.0257135118521,
      0.00218971274827, 0.0191985977382, 0.00236210105465, 0.0106140905815]),
    (['b2_5'],
     [0.00825995015344, 0.0194470245809, 0.0249482268617, 0.00537176175311,
      0.00731886287845, 0.00752180299311, 0.00661660334444, 0.0389706833806,
      0.0651928455219, 0.0428265200254, 0.00791772106042, 0.44467737224,
      0.0920904959423, 0.0592338708639, 0.0069376404609, 0.0187044744432,
      0.0135715643665, 0.0244456556953, 0.0222566530726, 0.0224096900147,
      0.0534135011737, 0.00488746097178, 0.012101046638, 0.00518022522231,
      0.00694661449746, 0.0132113490483, 0.0192673237896, 0.0144544745503,
      0.00684253270157, 0.0135311881264, 0.00684805707453, 0.015552260335,
      0.00810775831754, 0.0618854262432, 0.00645427352656, 0.0195095838985,
      0.026732560056, 0.0662074540376, 0.135463821924, 0.0396772149382,
      0.0528142301455, 0.0082538669997, 0.00659633528151, 0.0290595454297,
      0.107712385148, 0.00515327847365, 0.055798959988, 0.0323277284219,
      0.00221776144765, 0.0173795817505, 0.00232583932362, 0.00944638814806]),
]


class EventBasedHazardCase5TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'event_based')
    def test(self):
        cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
        job = self.run_hazard(cfg)
        cursor = models.getcursor('job_init')
        cursor.execute(GET_GMF_OUTPUTS % job.id)
        actual_gmfs = cursor.fetchall()
        self.assertEqual(len(actual_gmfs), len(EXPECTED_GMFS))
        for (actual_path, actual_gmf), (expected_path, expected_gmf) in zip(
                actual_gmfs, EXPECTED_GMFS):
            self.assertEqual(actual_path, expected_path)
            self.assertEqual(len(actual_gmf), len(expected_gmf))
            numpy.testing.assert_almost_equal(
                sorted(actual_gmf), sorted(expected_gmf))