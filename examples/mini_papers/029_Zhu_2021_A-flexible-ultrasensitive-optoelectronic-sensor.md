# A flexible ultrasensitive optoelectronic sensor array for neuromorphic vision systems

| 字段 | 内容 |
|---|---|
| 期刊 | Nature Communications |
| 年份 | 2021 |
| 引用量（Semantic Scholar） | 399 |
| 作者 | Qian-Bing Zhu, Bo Li, Dan Yang, Chi Liu, Shun Feng, Mao-Lin Chen, Yun Sun, Yaoyu Tian et al. |
| DOI | 10.1038/s41467-021-22047-w |
| 源文件 | 029_Zhu_2021_A-flexible-ultrasensitive-optoelectronic-sensor.pdf |

---


## ARTICLE 

https://doi.org/10.1038/s41467-021-22047-w 

**OPEN** 



# A flexible ultrasensitive optoelectronic sensor array for neuromorphic vision systems 

Qian-Bing Zhu<sup>1,2,9</sup> , Bo Li<sup>1,2,9</sup> , Dan-Dan Yang<sup>3</sup> , Chi Liu 1, Shun Feng1,4, Mao-Lin Chen 1, Yun Sun1, Ya-Nan Tian<sup>5</sup> , Xin Su<sup>6</sup> , Xiao-Mu Wang 6, Song Qiu 7✉, Qing-Wen Li7, Xiao-Ming Li3✉, Hai-Bo Zeng 3, Hui-Ming Cheng 1,2,8✉ & Dong-Ming Sun 1,2✉ 

The challenges of developing neuromorphic vision systems inspired by the human eye come not only from how to recreate the flexibility, sophistication, and adaptability of animal systems, but also how to do so with computational efficiency and elegance. Similar to biological systems, these neuromorphic circuits integrate functions of image sensing, memory and processing into the device, and process continuous analog brightness signal in real-time. High-integration, flexibility and ultra-sensitivity are essential for practical artificial vision systems that attempt to emulate biological processing. Here, we present a flexible optoelectronic sensor array of 1024 pixels using a combination of carbon nanotubes and perovskite quantum dots as active materials for an efficient neuromorphic vision system. The device has an extraordinary sensitivity to light with a responsivity of 5.1 × 10<sup>7</sup> A/W and a specific detectivity of 2 × 10<sup>16</sup> Jones, and demonstrates neuromorphic reinforcement learning by training the sensor array with a weak light pulse of 1 μW/cm<sup>2</sup> . 

> 1 Shenyang National Laboratory for Materials Science, Institute of Metal Research, Chinese Academy of Sciences, Shenyang, China. 2 School of Material Science and Engineering, University of Science and Technology of China, Hefei, China.<sup>3</sup> College of Materials Science and Engineering, Nanjing University of Science and Technology, Nanjing, China.<sup>4</sup> School of Physical Science and Technology, ShanghaiTech University, Shanghai, China.<sup>5</sup> College of Information Science and Engineering, Northeastern University, Shenyang, China.<sup>6</sup> School of Electronic Science and Engineering, Nanjing University, Nanjing, China. 

> 7 Suzhou Institute of Nano-Tech and Nano-Bionics, Chinese Academy of Sciences, Suzhou, China. 8 Tsinghua-Berkeley Shenzhen Institute, Tsinghua University, Shenzhen, China.<sup>9</sup> These authors contributed equally: Qian-Bing Zhu, Bo Li.<sup>✉</sup> email: sqiu2010@sinano.ac.cn; lixiaoming@njust.edu.cn; cheng@imr. ac.cn; dmsun@imr.ac.cn 

1 

NATURE COMMUNICATIONS | (2021) 12:1798 | https://doi.org/10.1038/s41467-021-22047-w | www.nature.com/naturecommunications 

<u>ARTICLE</u> 

NATURE COMMUNICATIONS <u>|</u> https://doi.org/10.1038/s41467-021-22047-w 

he human visual system is essential for both survival and learning. It is an efficient process in which the retina Tdetects light stimuli and pre-processes image information in parallel before the brain conducts more complex actions<sup>1–3</sup> . In recent years, digital vision systems, based on conventional complementary metal-oxide-semiconductor (CMOS) imagers or charge-coupled device (CCD) cameras<sup>4–9</sup> , have been rapidly developed to achieve the computer vision through extended interfaced digital processing units on serial or coarsely parallel structures<sup>10–13</sup> . However, these conventional digital artificial vision systems tend to consume a lot of power, and have a large size and high cost for practical applications, and neuromorphic vision sensors inspired by biological systems that integrate image sensing, memory, and processing are expected to overcome these disadvantages<sup>14–18</sup> . 

For the development of a high-performance neuromorphic vision system, optoelectronic sensors with ultra-high responsivity, detectivity, and signal-to-noise ratio are necessary to offer enhanced imaging capability under extreme dim light conditions<sup>19</sup> . For the selection of an active sensing material, the all-inorganic perovskite CsPbBr3-QDs have excellent optoelectronic response performance<sup>20–22</sup> , and CNTs can significantly improve the detection signal-to-noise ratio of the sensor due to the excellent carrier mobility and on/off ratio<sup>23–26</sup> . Both materials can be fabricated into uniform large-area films with excellent flexibility and stability, and the combination of these two materials provides a new strategy for the design and fabrication of high-performance neuromorphic vision sensors. 

Here, we report a flexible optoelectronic sensor array with 1024 pixels using a combination of CNTs and CsPbBr3-QDs as the active materials, which not only shows an extraordinary sensitivity to light but also has information storage and data preprocessing ability. The device shows a high responsivity of 5.1 × 10<sup>7</sup> A/W and an ultra-high specific detectivity of 2 × 10<sup>16</sup> Jones. It is also the first time that neuromorphic reinforcement learning has been experimentally demonstrated by training a highly integrated sensor array with a weak light pulse of 1 μW/cm<sup>2</sup> . Similar to biological systems, the photoreceptor, memory element, and computational node components share the same physical space in the array and process the information in parallel and in real-time, which makes them attractive for constructing artificial vision systems that attempt to emulate biological processing. 

### Results 

Device design and characterization. Figure 1a shows a schematic of the design of the phototransistor with a buried-gate structure, where the channel consists of high-purity (>99.9%) semiconducting CNTs (Supplementary Figs. 1–3) and perovskite CsPbBr3-QDs (Supplementary Fig. 4) that respectively act as active materials for electrical transport and photon absorption (‘Methods’ and Supplementary Figs. 5 and 6). The CNT random network covered by the uniformly-dispersed CsPbBr3-QDs (Fig. 1b, c) to ensure the formation of the high-quality CNT/ CsPbBr3-QD interface and gives a uniform device performance. Figure 1d shows typical transfer characteristics (IDS–VGS) of the phototransistor in the dark and under various lighting power densities (P). The strong photo-response observed shows a largely positive shift in the transfer characteristic curves as the lighting power density increases, and a maximum off-current ratio of 3.6 × 10<sup>6</sup> has been achieved for the dark and illuminated conditions (Supplementary Fig. 7). But channel materials composed only of CsPbBr3-QD or CNT cannot meet the high optical response requirements (Supplementary Fig. 8). The output (IDS– VDS) characteristics at various lighting power densities for fixed VGS = 5 and 0 V are also measured (Supplementary Fig. 9), 

indicating that the optoelectronic performance of the phototransistor is related to the lighting power density. 

Figure 1e shows the energy band diagram at the CNT/ CsPbBr3-QD interface for the photogating mechanism. The top panel shows that a built-in electric field that equilibrates the Fermi levels was formed, which leads to band bending at the interface due to the energy band mismatch (Supplementary Fig. 10)<sup>27,28</sup> , contributing to the negative shift observed in the dark of the transfer characteristics after spin-coating CsPbBr3QDs on the CNTs (Supplementary Fig. 11). For the light-on state in the bottom panel, a highly effective dissociation of photogenerated electron-hole pairs occur at the interface between the CNTs and the QDs, as shown in the steady-state and transient photoluminescence (PL) spectra (Supplementary Fig. 12). The longer the exciton lifetime of the CsPbBr3-QDs, the stronger its fluorescence intensity. Therefore, the exciton separation at the CNT/CsPbBr3-QD interface is faster than that of the CsPbBr3QDs, which is related to the shorter exciton lifetime. The holes separated by the built-in electric field are transferred from the valence band of the QDs to that of the CNTs, and the electrons remain trapped in the CsPbBr3-QDs. Therefore, the negativelycharged QDs induce positive carriers in the CNT film through capacitive coupling that shifts transfer curves in the positive direction<sup>29,30</sup> . 

Optoelectronic characteristics. Figure 2 shows the detailed optoelectronic performance to show the figures of merit of the phototransistor. The responsivity (R) decreases with increasing P because of the saturated absorption when P is large, reaching the maximum value of 5.1 × 10<sup>7</sup> A/W at the minimum P of 0.01 μW/cm<sup>2</sup> (Fig. 2a). The dependence of the responsivity on P under various VGS of −5, 0, and +5 V are measured, as shown in Supplementary Fig. 15. It can be found that the photocurrent and responsivity are very similar, especially in the cases of higher lighting power densities, which indicates that the negatively-charged QDs are the dominant factor leading to the increase in current. The external quantum efficiency (EQE) also shows a similar downward tendency and reaches the highest value of 1.6 × 10<sup>10</sup> %. As a figure of merit used to characterize performance, the specific detectivity (D*) of 2 × 10<sup>16</sup> Jones is achieved in Fig. 2b, owing to the ultrahigh on- and offcurrent ratio and the high response to weak light with a wavelength of 405 nm (the case of 516 nm, in Supplementary Fig. 17). To benchmark our device, we compared its performance with those of devices constructed of various low-dimensional (0D<sup>28,31,32</sup> , 1D<sup>33,34</sup> , and 2D<sup>35–37</sup> ) materials, organic<sup>38,39</sup> , and hybrid<sup>27,40–48</sup> materials in Fig. 2c, and our device shows an ultra-high detectivity for reported devices made with various materials and structures and a comparable responsivity to the highest value for graphene-PbS QDs<sup>40</sup> . 

Figure 2d shows the switching characteristics of the phototransistor illuminated by a 516 nm light pulse and triggered by applying a short gate pulse voltage from +5 to 0 V to cause a discharge of trapped charge carriers<sup>40,49,50</sup> , which results in a rapid decay of photocurrent. The measured response indicates a rise time of 3.3 ms and a fast decay time of 1.1 ms at 0.78 W/cm<sup>2</sup> (Supplementary Figs. 18–20). In addition, the fabricated device shows long-term stability after being stored in ambient air for more than 8 months (Supplementary Fig. 21) and excellent flexibility when stress is applied, and the IDS–VGS curves are almost identical for bending strains (ε) from 0 to 0.4% (Supplementary Figs. 22 and 23). 

Light-tunable synaptic characteristics. The phototransistor shows memory characteristics and light-dose-dependent response characteristics (Supplementary Figs. 24 and 13), which allow us to mimic the basic features of synaptic plasticity in emulating the 

2 

NATURE COMMUNICATIONS | (2021) 12:1798 | https://doi.org/10.1038/s41467-021-22047-w | www.nature.com/naturecommunications 

<u>ARTICLE</u> 

NATURE COMMUNICATIONS <u>|</u> https://doi.org/10.1038/s41467-021-22047-w 



<!-- Start of picture text -->
a b c<br>Channel S 21 nm<br>G<br>D<br>-21 nm<br>d e<br>10 -4<br>CNT CsPbBr3-QD<br>1.7 EC<br>10 -6 0.25 EV<br>10 -8 0.1<br>CNT CsPbBr3-QD<br>EC Trapping<br>10 -10<br>EV<br>0 μW/cm 2 h v<br>10 -12<br>-4 -2 0 2 4<br>V GS (V)<br>CsPbBr3 Light<br>Al2O3<br>Source<br>CNT<br>Substrate<br>Gate<br>Drain<br> (A) I DS<br><!-- End of picture text -->

Fig. 1 Device design and characterization. a Schematic of the phototransistor with a CNT/CsPbBr3-QD channel. b Scanning electron microscope (SEM) image of a CNT film (scale bar, 1 μm). Inset: optical microscope image of the fabricated device (scale bar, 50 μm). c Atomic force microscope (AFM) image of a CsPbBr3-QD film (scale bar, 250 nm). d Room temperature transfer characteristics (IDS – VGS) of the device at VDS = 1 V using a collimated incident beam of laser light with a wavelength λ of 516 nm and power densities (P) increasing from 0 to 1.7 μW/cm<sup>2</sup> . e Energy band diagram at the light-off (top panel) and light-on states (bottom panel). 

learning and memory functions of the human brain, including a transition from short-term plasticity (STP) to long-term plasticity (LTP) (Supplementary Figs. 25 and 26). The effect of paired-pulse facilitation (PPF) among the basic synaptic characteristics is demonstrated in this device by applying two successive optical pulses with a P of 48 μW/cm<sup>2</sup> , a pulse width of 20 ms, and different pulse intervals, as shown in Fig. 2e. The PPF ratio is defined by the ratio of A2 to A1, where A1 and A2 are, respectively, the peak amplitudes of the current from the first and second optical pulses. When the optical pulse is applied to the phototransistor, the current in the CNT film channel increases and the trapped photogenerated electrons inside the perovskite QD layer take a long time to decay. After application of the second photonic pulse, a higher internal electric field as a result of more trapped electrons induces a higher current level. Furthermore, the PPF index decreases gradually when the pulse interval increases, and a 1 s interval generates a PPF index of more than 180%. Figure 2f shows the induction of long-term potentiation during 500 light pulses at various lighting power densities to demonstrate the persistent strengthening of synaptic characteristics, which means that the optical signal was gradually learned and remembered by our phototransistor. The current increases steadily with an increase in the number of pulse stimulations, and the number of optical pulses needed to achieve a target synaptic weight is reduced for a higher lighting power density and speeds up the associated learning process. 

Flexible optoelectronic sensor array. Figure 3 shows a 32 × 32 sensor array and its functional demonstration in a neuromorphic vision system. From macro- to micro-levels, the photographic images (Fig. 3a–c and Supplementary Fig. 28) show the array chip mounted on a printed circuit board (PCB), the bonding wires and interconnections in the circuit, and the individual sensor unit with a similar construction to the aforeintroduced phototransistor. All devices with 1024 pixels in the 

sensor array have been tested and the device yield is 100%, demonstrating the excellent performance uniformity of the device (Supplementary Fig. 29), which is crucial for high-quality image sensing ability. 

It was found that the on-current of a single phototransistor increased steadily with an increase in the pulse number of light (Fig. 2f), and the pulse number was reduced for a higher lighting power density to achieve the target synaptic weight, thereby representing the persistent strengthening of synaptic characteristics. The on-currents of 1024 pixels in the sensor array have excellent uniformity, which enables high-quality image sensing, and the larger on-current represents a deeper impression in the evolution of learning and training of images, which allows us to demonstrate the function of neuromorphic pattern reinforcement. This behavior is similar to human vision, where the features of familiar faces are clearer than the features of a strange face occasionally seen (3d). After training 0, 10, 20, 50, 100, and 200 pulses with an ultra-weak light (1 μW/cm<sup>2</sup> ), the weight map of the sensor array obtained shows different resemblance degrees, as well as image sharpness to the input number 8 pattern (Fig. 3e). The calculated accuracy between the ideal input picture and the trained weight map increases with the increase of the number of training pulses, and reached 95% for the case of 200 pulses (Supplementary Fig. 34). In addition, Fig. 3f shows the weight map of the sensor array after training with 10 pulses under a 405 nm light with various lighting power densities, indicating that the higher lighting density can speed up the pattern learning process. Therefore, by training a highly integrated sensor array with weak light pulses, the function of neuromorphic reinforcement learning has been demonstrated experimentally. This is similar to what happens in interpersonal communication, that is, the more you deal with someone, the more facial features you know. We carried out a simulation to mimic the evolution of the learning process of a human face (Fig. 3g) on the basis of the experimental synaptic characteristics in Fig. 3e (Supplementary 

3 

NATURE COMMUNICATIONS | (2021) 12:1798 | https://doi.org/10.1038/s41467-021-22047-w | www.nature.com/naturecommunications 

<u>ARTICLE</u> 

NATURE COMMUNICATIONS <u>|</u> https://doi.org/10.1038/s41467-021-22047-w 



<!-- Start of picture text -->
a b<br>10 11 10 11 10 17<br>10 9 10 9<br>10 15<br>10 7 10 7<br>10 13<br>10 5 10 5<br>10 11<br>10 3 10 3<br>10 1 10 1 10 9<br>10 -7 10 -5 10 -3 10 -1 10 -7 10 -5 10 -3 10 -1<br>Power density (W/cm 2 ) Power density (W/cm 2 )<br>c d<br>10 17<br>This Work Optical<br>10 15 [31] [47] Electrical A<br>[40] [43] [46] 10 -6<br>10 13 [42] [44] [48] [32]<br>[35]<br>[41]<br>10 11 [38] [39] [45] [49] 10 -8<br>[36] 0 D<br>10 9 [28] [27] [50] 1 D2 D 10 -10<br>Organics<br>10 7<br>[37] Hybrids 10 -12<br>10 0 10 2 10 4 10 6 10 8 0 200 400 600 800 1000<br>Responsivity (A/W) Time (s)<br>e f<br>8<br>180 Optical μW48/cm2 74.5<br>6<br>20 25.2<br>150<br>10 A2 A1 4 15<br>7.4<br>0 30 60<br>120 Time (s) 2 4.9 μW/cm 2<br>0<br>0 20 40 60 80 0 100 200 300 400 500<br>Pulse interval (s) Pulse number<br>EQE (%)<br>Responsivity (A/W) Detectivity (Jones)<br> (A) I DS<br>Detectivity (Jones)<br> (nA) I DS<br> (μA) I DS<br>PPF index (%)<br><!-- End of picture text -->

Fig. 2 Optoelectronic and synaptic characteristics. a Dependence of the responsivity (R) and the external quantum efficiency (EQE) on the lighting power density (P). R ¼ Iph=P�Lch ´ Wch�, where Iph is the photocurrent, Lch and Wch are, respectively, the channel length (20 μm) and channel width (100 μm). EQE ¼ hcR=eλ, where h is the Planck constant, c the speed of light, and e the electron charge. λ = 405 nm. b Dependence of the specific detectivity (D*) on the P. D<sup>�</sup> ¼ R�Lch ´ Wch�1=2=�Sn�1=2, where Sn is the noise power density (Supplementary Fig. 16). c Benchmark of the device performance demonstrating an ultra-high detectivity among reported devices made using various materials and structures. d Switching characteristics of the device under a 516 nm light with a P of 0.78 W/cm<sup>2</sup> and a reset voltage pulse (+5 to 0 V, pulse width 100 ms) to the gate electrode. VDS = 1 V, VGS = 5 V. e PPF index decreases gradually when the pulse interval increases. Inset: PPF achieved by two successively applied optical pulses (48 μW/cm<sup>2</sup> , pulse width 20 ms, pulse interval 10 s). f Long-term potentiation with 500 optical pulses (pulse width, 20 ms; pulse interval, 500 ms) at various lighting power densities. 

Figs. 35 and 36), and verified that more facial features are learned as the number of training pulses increases (Supplementary Fig. 37). 

### Discussion 

We have demonstrated a flexible optoelectronic sensor array with special features including a high integrated density of 1024 pixels, ultra-sensitivity with an ultra-high specific detectivity for visible light, and the ability for both image sensing and bio-inspired information processing. The active channel consisting of semiconducting carbon nanotubes and perovskite CsPbBr3 quantum dots plays the key roles in the photogenerated carrier separation and transport, achieving a high responsivity of 5.1 × 10<sup>7</sup> A/W and 

an ultra-high specific detectivity of 2 × 10<sup>16</sup> Jones. The optoelectronic sensor simultaneously acts as an artificial photoreceptor and a biological synapse, and, thus, directly responds to optical stimuli and performs light-tunable synaptic plasticity for functional preprocessing. These results provide motivation for the development of artificial neuromorphic visual systems to simulate the flexibility, complexity, and adaptability of biological vision systems. 

### Methods 

Preparation of semiconducting CNTs and CsPbBr3-QDs. The raw arc-discharge CNT purchased from Carbon Solution Inc. (https://carbonsolution.com/products/ ap-swnt) has a narrow diameter distribution with a peak value of 1.55 ± 0.1 nm and a bundle length of 1–5 μm. High-purity (>99.9%) semiconducting CNTs were sorted by mixing bulk CNTs with a dispersant 9-(1-octylonoyl)-9H-carbazole-2,7- 

4 

NATURE COMMUNICATIONS | (2021) 12:1798 | https://doi.org/10.1038/s41467-021-22047-w | www.nature.com/naturecommunications 

<u>ARTICLE</u> 

NATURE COMMUNICATIONS <u>|</u> https://doi.org/10.1038/s41467-021-22047-w 



<!-- Start of picture text -->
a b c<br>Gate<br>Drain Source<br>Channel<br>d<br>Visual cortex<br>e<br>I DS (nA)<br>500<br>0<br>Input picture Initial state 10 pulses 20 pulses 50 pulses 100 pulses 200 pulses<br>f<br>I DS (μA)<br>3<br>0<br>Input picture Initial state 4.0 μW/cm 2 0.3 mW/cm 2 1.0 mW/cm 2 2.5 mW/cm 2 4.0 mW/cm 2<br>g<br>Input picture Initial state 10 pulses 20 pulses 50 pulses 100 pulses 200 pulses<br>Stranger<br>Familiar<br><!-- End of picture text -->

Fig. 3 Optoelectronic sensor array. a A sensor array chip with wire bonding on a PCB (scale bar, 5 mm). b Optical micrograph of a 32 × 32 sensor array (scale bar, 500 μm). c Magnified image of an individual sensor unit with a channel dimension of 20 × 20 μm<sup>2</sup> (scale bar, 20 μm). d Schematics of the impression of human visual systems when strange and familiar faces are observed. e Measured training weight results of a number 8 pattern in the initial state and after training with 10, 20, 50, 100, and 200 pulses under 405 nm light with a lighting power density of 1 μW/cm<sup>2</sup> (pulse width, 250 ms; pulse interval, 250 ms). f Measured training weight results of the sensor array after training with 10 pulses under a 405 nm light with various lighting power densities of 4.0 μW/cm<sup>2</sup> , 0.3 mW/cm<sup>2</sup> , 1.0 mW/cm<sup>2</sup> , 2.5 mW/cm<sup>2</sup> , and 4.0 mW/cm<sup>2</sup> (pulse width, 250 ms; pulse interval, 250 ms). g Simulation results of a man’s face in the initial state and after training processes. 

diyl (PCz) in a xylene solution, followed by ultrasonic stirring for 30 min, and then centrifugation at 45,000 g for 1 h to remove CNT bundles and insoluble substances. The supernatants were collected for use as the channel materials<sup>51</sup> . For the preparation of the CsPbBr3-QDs, PbBr2, 1-octadecene, oleic acid, and oleylamine were loaded into a three-neck flask and degassed for 30 min at 120 °C under an Ar flow. After complete dissolution of the PbBr2, the temperature was increased to 170 °C where it was maintained for 30 min under an Ar atmosphere. The preheated Csoleate solution was swiftly injected into the transparent precursor solution for a 5 s reaction, and the mixture was cooled using a water bath. Ethyl acetate was then added to the crude solution with a volume ratio of 1:3 and the mixture was centrifuged at 16,000 g for 1 min, and the procedure was repeated once for better purification, and the final CsPbBr3-QDs were dispersed in hexane to obtain a clear solution<sup>52</sup> . 

Device fabrication on a rigid substrate. Gate electrodes (Ti/Au: 5/50 nm) were fabricated by standard photolithography, electron-beam evaporation (EBV), and lift-off processes. A 40-nm-thick Al2O3 dielectric layer was then deposited on the substrate by an atomic layer deposition (ALD) technique (trimethylaluminum and water as precursors, 150 °C), followed by opening a window by reactive ion etching (50 sccm CF4, 5.0 Pa, 100 W, 10 min). Next, source and drain electrodes were formatted on the dielectric layer by the aforementioned method. The substrate was then coated with a monolayer of hexamethyldisilazane and immersed in the semiconducting CNT solution at 60 °C for 2 h. The substrate loaded with the CNT film was washed in toluene and isopropyl alcohol (IPA) for 5 min each. Finally, the CNT film was patterned by photolithography and oxygen plasma etching (180 sccm O2, 200 W, 2 min) to form channels, and the solution of CsPbBr3-QDs was spin-coated onto the top of the channels at 3000 rpm for 60 s, which avoids the 

5 

NATURE COMMUNICATIONS | (2021) 12:1798 | https://doi.org/10.1038/s41467-021-22047-w | www.nature.com/naturecommunications 

<u>ARTICLE</u> 

NATURE COMMUNICATIONS <u>|</u> https://doi.org/10.1038/s41467-021-22047-w 

performance degradation of the CsPbBr3-QDs caused by polar solvents (e.g., Remover PG and isopropyl alcohol) used in the fabrication processes. 

Fabrication of a sensor array on a flexible substrate. A flexible sensor array was fabricated on a 125-µm-thick polyethylene naphthalate (PEN) substrate (Teijin DuPont Films) (Supplementary Fig. 27). The substrate was first heated at 190 °C for 3 h and washed by a solvent of Remover PG (Microchem) and IPA for 20 min each to remove particles on the substrate generated during the preheating. Next, the gate electrodes and interconnections (Ti/Au: 5/50 nm) were formatted by photolithography, EBV, and lift-off processes. Subsequently, an insulating 80-nmthick Al2O3 layer was deposited on the substrate by an ALD technique, followed by opening a window by wet etching using phosphoric acid at 70 °C for 6 min. Finally, the source, drain electrodes, interconnections, and semiconducting channels were fabricated by the same processes using for the device on the rigid substrate. 

Characterization. The materials and devices were characterized using an optical microscope (Nikon Eclipse LV100ND), an SEM (FEI Nova NanoSEM430, acceleration voltage of 1 kV), an AFM (Bruker Dimension Icon), and a UV–Vis–NIR spectroscope (Varian Cary 5000). The electrical and optoelectronic performances were measured using a semiconductor analyzer (Agilent B1500A), a probe station (Cascade M150), an input signal generator (Tektronix AFG 3022C), an oscilloscope (Tektronix MSO 2024B), and a laser diode controller (Thorlabs ITC4001, using laser excitations of 405 and 516 nm) in a dark room at room temperature. The noise was measured by a noise measurement system (PDA NC300L, 100 kHz bandwidth). With the help of special mask to avoid crosstalk issues (Supplementary Fig. 30), the electrical performance of the 1024 phototransistors in the optoelectronic sensor array was automatically measured using a home-built transistor array test system (Agilent B1500A and Keysight 34980A) controlled by a self-developed program, and the data analysis and image processing were carried out using MATLAB (Supplementary Figs. 31–33). 

Statement of consent to publication of human face. An image of a recognizable person in Fig. 3g and Supplementary Fig. 37c is the face of Qian-Bing Zhu who is the first author of this paper. The authors affirm that human research participants provided informed consent for publication of the images in Fig. 3g and Supplementary Fig. 37c. 

### Data availability 

The data that support the findings of this study are available at Zenodo (2021), https:// doi.org/10.5281/zenodo.4540948. 

### Received: 30 October 2020; Accepted: 25 February 2021; 



### References 

1. Pocock, D. C. D. Sight and knowledge. Trans. Inst. Br. Geogr. 6, 385–393 (1981). 

2. Kolb, H. How the retina works: much of the construction of an image takes place in the retina itself through the use of specialized neural circuits. Am. Sci. 91, 28–35 (2003). 

3. Eldred, K. C. et al. Thyroid hormone signaling specifies cone subtypes in human retinal organoids. Science 362, eaau6348 (2018). 

4. Lee, G. J., Choi, C., Kim, D. H. & Song, Y. M. Bioinspired artifcial eyes: optic components, digital cameras, and visual prostheses. Adv. Funct. Mater. 28, 1705202 (2018). 

5. Ko, H. C. et al. A hemispherical electronic eye camera based on compressible silicon optoelectronics. Nature 454, 748–753 (2008). 

6. Song, Y. M. et al. Digital cameras with designs inspired by the arthropod eye. Nature 497, 95–99 (2013). 

7. Choi, C. et al. Human eye-inspired soft optoelectronic device using highdensity MoS2-graphene curved image sensor array. Nat. Commun. 8, 1664 (2017). 

8. Zhang, K. et al. Origami silicon optoelectronics for hemispherical electronic eye systems. Nat. Commun. 8, 1782 (2017). 

9. Gu, L. et al. A biomimetic eye with a hemispherical perovskite nanowire array retina. Nature 581, 278–282 (2020). 

10. Wu, C. & Chiu, C. A new structure of the 2-D silicon retina. IEEE J. SolidState Circuits 30, 890–897 (1995). 

11. Leon-Salas, W. D. et al. A CMOS imager with focal plane compression using predictive coding. IEEE J. Solid-State Circuits 42, 2555–2572 (2007). 

12. Shoushun, C. & Bermak, A. Arbitrated time-to-first spike CMOS image sensor with on-chip histogram equalization. IEEE Trans. Very Large Scale Integr. (VLSI) Syst. 15, 346–357 (2007). 

13. LeCun, Y., Bengio, Y. & Hinton, G. Deep learning. Nature 521, 436–444 (2015). 

14. Giacomo Indiveri, R. D. Neuromorphic vision sensors. Science 288, 1189–1190 (2000). 

15. Wang, Y. et al. Photonic synapses based on inorganic perovskite quantum dots for neuromorphic computing. Adv. Mater. 30, 1802883 (2018). 

16. Zhou, F. et al. Optoelectronic resistive random access memory for neuromorphic vision sensors. Nat. Nanotechnol. 14, 776–782 (2019). 

17. Mennel, L. et al. Ultrafast machine vision with 2D material neural network image sensors. Nature 579, 62–66 (2020). 

18. Wang, C. et al. Gate-tunable van der Waals heterostructure for reconfigurable neural network vision sensor. Sci. Adv. 6, eaba6173 (2020). 

19. Chai, Y. In-sensor computing for machine vision. Nature 579, 32–33 (2020). 20. Song, J. et al. Quantum dot light-emitting diodes based on inorganic perovskite cesium lead halides (CsPbX3). Adv. Mater. 27, 7162–7167 (2015). 

21. Song, J. et al. Monolayer and few-layer all-inorganic perovskites as a new family of two-dimensional semiconductors for printable optoelectronic devices. Adv. Mater. 28, 4861–4869 (2016). 

22. Li, X. et al. Constructing fast carrier tracks into flexible perovskite photodetectors to greatly improve responsivity. ACS Nano 11, 2015–2023 (2017). 

23. Sun, D. et al. Flexible high-performance carbon nanotube integrated circuits. Nat. Nanotechnol. 6, 156–161 (2011). 

24. Zhao, T. et al. Flexible 64 × 64 pixel AMOLED displays driven by uniform carbon nanotube thin-film transistors. ACS Appl. Mater. Interfaces 11, 11699–11705 (2019). 

25. Hills, G. et al. Modern microprocessor built from complementary carbon nanotube transistors. Nature 572, 595–602 (2019). 

26. Qu, T. et al. A flexible carbon nanotube sen-memory device. Adv. Mater. 32, 1907288 (2020). 

27. Park, S. et al. Significant enhancement of infrared photodetector sensitivity using a semiconducting single-walled carbon nanotube/C60 phototransistor. Adv. Mater. 27, 759–765 (2015). 

28. Dong, Y. et al. Improving all-inorganic perovskite photodetectors by preferred orientation and plasmonic effect. Small 12, 5622–5632 (2016). 

29. Stranks, S. D. et al. Recombination kinetics in organic-inorganic perovskites: excitons, free charge, and subgap states. Phys. Rev. Appl. 2, 034007 (2014). 

30. Fang, H. & Hu, W. Photogating in low dimensional photodetectors. Adv. Sci. 4, 1700323 (2017). 

31. Liu, X. et al. Low-voltage photodetectors with high responsivity based on solution-processed micrometer-scale all-inorganic perovskite nanoplatelets. Small 13, 1700364 (2017). 

32. Li, X. et al. Healing all-inorganic perovskite films via recyclable dissolutionrecyrstallization for compact and smooth carrier channels of optoelectronic devices with high stability. Adv. Funct. Mater. 26, 5903–5912 (2016). 

33. Zeng, Q. et al. Carbon nanotube arrays based high-performance infrared photodetector. Opt. Mater. Express 2, 839–848 (2012). 

34. Asuo, I. M. et al. High-performance pseudo-halide perovskite nanowire networks for stable and fast-response photodetector. Nano Energy 51, 324–332 (2018). 

35. Tu, L. et al. Ultrasensitive negative capacitance phototransistors. Nat. Commun. 11, 101 (2020). 

36. Kufer, D. & Konstantatos, G. Highly sensitive, encapsulated MoS2 photodetector with gate controllable gain and speed. Nano Lett. 15, 7307–7313 (2015). 

37. Wang, T. et al. High-performance WSe2 phototransistors with 2D/2D ohmic contacts. Nano Lett. 18, 2766–2771 (2018). 

38. Wu, S. et al. Visible-blind ultraviolet sensitive photodiode with high responsivity and long term stability. Appl. Phys. Lett. 97, 023306 (2010). 

39. Lan, Z. et al. Near-infrared and visible light dual-mode organic photodetectors. Sci. Adv. 6, eaaw8065 (2020). 

40. Konstantatos, G. et al. Hybrid graphene-quantum dot phototransistors with ultrahigh gain. Nat. Nanotechnol. 7, 363–368 (2012). 

41. Chen, Y. et al. High-performance inorganic perovskite quantum dot-organic semiconductor hybrid phototransistors. Adv. Mater. 29, 1704062 (2017). 

42. Zou, C. et al. A highly sensitive UV–vis–NIR all‐inorganic perovskite quantum dot phototransistor based on a layered heterojunction. Adv. Opt. Mater. 6, 1800324 (2018). 

43. Wu, H. et al. All-inorganic perovskite quantum dot-monolayer MoS2 mixeddimensional van der Waals heterostructure for ultrasensitive photodetector. Adv. Sci. 5, 1801219 (2018). 

44. Liu, Z. et al. Photoresponsive transistors based on lead-free perovskite and carbon nanotubes. Adv. Funct. Mater. 30, 1906335 (2020). 

45. Wu, X. et al. Distinguishable detection of ultraviolet, visible, and infrared spectrum with high-responsivity perovskite-based flexible photosensors. Small 14, 1800527 (2018). 

46. Hu, C. et al. Synergistic effect of hybrid PbS quantum dots/2D-WSe2 toward high performance and broadband phototransistors. Adv. Funct. Mater. 27, 1603605 (2017). 

6 

NATURE COMMUNICATIONS | (2021) 12:1798 | https://doi.org/10.1038/s41467-021-22047-w | www.nature.com/naturecommunications 

<u>ARTICLE</u> 

NATURE COMMUNICATIONS <u>|</u> https://doi.org/10.1038/s41467-021-22047-w 

47. Kufer, D. et al. Hybrid 2D-0D MoS2 -PbS quantum dot photodetectors. Adv. Mater. 27, 176–180 (2015). 

48. Lee, Y. et al. High-performance perovskite-graphene hybrid photodetector. Adv. Mater. 27, 41–46 (2015). 

49. Jeon, S. et al. Gated three-terminal device architecture to eliminate persistent photoconductivity in oxide semiconductor photosensor arrays. Nat. Mater. 11, 301–305 (2012). 

50. Lopez-Sanchez, O. et al. Ultrasensitive photodetectors based on monolayer MoS2. Nat. Nanotechnol. 8, 497–501 (2013). 

51. Gu, J. et al. Solution-processable high-purity semiconducting SWCNTs for large-area fabrication of high-performance thin-film transistors. Small 12, 4993–4999 (2016). 

52. Yang, D. et al. CsPbBr3 quantum dots 2.0: benzenesulfonic acid equivalent ligand awakens complete purification. Adv. Mater. 31, 1900767 (2019). 

were responsible for characterizing the materials. X.S. carried out characterizations of noise power density supervised by X.-M.W. D.-D.Y. prepared the solution of CsPbBr3QDs supervised by X.-M.L. and H.-B.Z. S.Q. and Q.-W.L. prepared the semiconducting CNT solution. Q.-B.Z. and D.-M.S. wrote the paper. All authors discussed the results and commented on the manuscript. 

### Competing interests 

The authors declare no competing interests. 

### Additional information 

Supplementary information The online version contains supplementary material available at https://doi.org/10.1038/s41467-021-22047-w. 

Correspondence and requests for materials should be addressed to S.Q., X.-M.L., H.-M. C. or D.-M.S. 

### Acknowledgements 

This work was supported by the National Key Research and Development Program of China (2020YFA0714702, 2016YFB041104), the National Natural Science Foundation of China (No. 61574143, 51532008, 61704175, 51502304, 22075312, 21773292, and 61874054), the Strategic Priority Research Program of Chinese Academy of Sciences (XDB30000000), the Key Research Program of Frontier Sciences of the Chinese Academy of Sciences (ZDBS-LY-JSC027, QYZDB-SSW-SLH031), Liaoning Revitalization Talents Program (XLYC1807109), the Thousand Talent Program for Young Outstanding Scientists, Key-Area Research and Development Program of Guangdong Province (2019B010934001), the Shandong Natural Science Foundation of China (ZR2019ZD49), and the projects supported by Shenyang National Laboratory for Materials Science, Institute of Metal Research, Chinese Academy of Sciences and State Key Laboratory of Luminescence and Applications, Chinese Academy of Sciences (L2019F28, Project Young Merit Scholars, SKLA-2019-03). The authors wish to thank Qin-Yi Zhang, Ya-Hui Li, Jin-Bo Wu, and Hua-Hua Li for valuable discussions. We thank Feng-Xiu Yuan for kind help on data processing. 

### Author contributions 

H.-M.C. and D.-M.S. conceived the idea and supervised the project. Q.-B.Z. and B.L. were equal major contributors to this work. Q.-B.Z. and B.L. performed the device fabrication. Q.-B.Z. carried out electrical and optoelectronic characterizations. C.L. proposed the mechanism of the device assisted by Q.-B.Z. Y.-N.T. carried out the simulation. Q.-B.Z. and B.L. contributed to the 3D schematic and illustration (Figs. 1a and 3d). Y.S. and B.L carried out the ALD depositions. Q.-B.Z., B.L., S.F., and M.-L.C. 

Peer review information Nature Communications thanks Yang Chai, Su-Ting Han, and Deok-kee Kim for their contribution to the peer review of this work. Peer reviewer reports are available. 

Reprints and permission information is available at http://www.nature.com/reprints 

Publisher’s note Springer Nature remains neutral with regard to jurisdictional claims in published maps and institutional affiliations. 

Open Access This article is licensed under a Creative Commons Attribution 4.0 International License, which permits use, sharing, adaptation, distribution and reproduction in any medium or format, as long as you give appropriate credit to the original author(s) and the source, provide a link to the Creative Commons license, and indicate if changes were made. The images or other third party material in this article are included in the article’s Creative Commons license, unless indicated otherwise in a credit line to the material. If material is not included in the article’s Creative Commons license and your intended use is not permitted by statutory regulation or exceeds the permitted use, you will need to obtain permission directly from the copyright holder. To view a copy of this license, visit http://creativecommons.org/ licenses/by/4.0/. 

© The Author(s) 2021 

7 

NATURE COMMUNICATIONS | (2021) 12:1798 | https://doi.org/10.1038/s41467-021-22047-w | www.nature.com/naturecommunications 

