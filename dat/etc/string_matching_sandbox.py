
#from fuzzywuzzy import fuzz

def remove_phrase(pdf_desc, site_desc, smallest_phrase):
    #print("removing phrase \n")

    # Decrementing i from (len(site_desc)) to 0

    for i in range(len(site_desc), smallest_phrase, -1) :
        # If if this substring of site_disc exists within our pdf_desc
        if(site_desc[0:i] in pdf_desc) :
            site_desc_with_colon = site_desc[i:len(site_desc)]
            site_desc = site_desc_with_colon.removeprefix("; ").removeprefix("-").removeprefix(" ")
            #print(f"i: {i}, site_desc: {site_desc}")
            break


    #print(site_desc)
    return site_desc

def get_attributes(pdf_desc, site_desc, max_components = 8, smallest_phrase = 7) :
    shorter_site_desc = site_desc

    for i in range(0, max_components) :
        shorter_site_desc = remove_phrase(pdf_desc, shorter_site_desc, smallest_phrase)
        #print("--------------------")
        #print(shorter_site_desc)
    return shorter_site_desc

# You should functionalize all of the code!
pdf_desc = "Arcol LG-650 polyether polyol is a 260-molecular-weight polypropylene oxide-based triol. The terminal end-groups are predominantly secondary hydroxyls and have a relatively low reactivity. It is compatible with some polyether polyols and can be blended with other diols or triols to achieve desirable modifications of product properties. Arcol LG-650 polyol is typically used in a broad range of urethane foam and other applications, including structural coatings, hard coatings, potting compounds, and thermal break. As with any product, the use of Arcol LG-650 polyol in a given application must be tested (including but not limited to field testing) in advance by the user to determine suitability"
site_desc = "polyether polyol; 260-molecular weight polypropylene oxide-based triol; functionality 3; hydroxyl number 650 mg KOH/g; molecular weight 260; viscosity 820 cps @ 25°C"


print("-------")
print(f"initial description from pdf:\n{pdf_desc}")
print("-------")
print(f"initial description from website:\n{site_desc}")
print("-------")

max_components = 8
smallest_phrase = 7
parsed_attributes = get_attributes(pdf_desc, site_desc, max_components, smallest_phrase)

parsed_description = site_desc.removesuffix(f"; {parsed_attributes}")
print(f"parsed description:\n{parsed_description}")
print("-------")
print(f"parsed attributes:\n{parsed_attributes}")
print("-------")
