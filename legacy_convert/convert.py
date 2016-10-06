"""
Convert legacy problem.xml to new exercise.xml
"""
import sys
import os
from lxml import etree


def get_xmltree(path):
    xmlfile = path
    parser = etree.XMLParser(remove_blank_text=True)
    try:
        root = etree.parse(xmlfile, parser)
        return root
    except etree.XMLSyntaxError as e:
        raise ExerciseParseError(e)


def xprint(el):
    if isinstance(el, list):
        for x in el:
            print(etree.tostring(x, pretty_print=True, encoding="unicode"))
    else:
        print(etree.tostring(el, pretty_print=True, encoding="unicode"))


def add_converted_text(root, newroot, oldname, newname):
    old = root.find(oldname)
    if old is not None:
        new = etree.SubElement(newroot, newname)
        new.text = old.text
        return new


def convert(exercise_path):
    inxml = get_xmltree(exercise_path)
    # print(etree.tostring(inxml, pretty_print=True, encoding="unicode"))
    problem = inxml.getroot()
    if problem.tag != 'problem':
        raise Exception("Root element is not <problem>")
    # for child in problem.getchildren():
    #    print(inxml.getpath(child))

    out = etree.Element('exercise')
    out_tree = etree.ElementTree(out)

    nametag = None
    if problem.find("name") is not None:
        nametag = "name"
    if problem.find("name7") is not None:
        nametag = "name7"
    if nametag:
        newname = add_converted_text(problem, out, nametag, "exercisename")
        newname.text = newname.text.replace('Dynamics ', '')
        newname.text = newname.text.replace('Statics ', '')

    problemtext = problem.xpath("/problem/question/text/text()")
    if problemtext:
        exercisetext = etree.SubElement(out, 'text')
        exercisetext.text = problemtext[0].strip()
        add_converted_text(problem, exercisetext, "figure", "figure")

    oldsolution = problem.xpath("/problem/osolution/image/text()")
    if oldsolution:
        newsolution = etree.SubElement(out, 'solution')
        asset = etree.SubElement(newsolution, 'asset', {'name': 'Lösning'})
        asset.text = oldsolution[0].strip()

    questions = problem.xpath("/problem/thecorrectanswer")

    ingress = list(filter(lambda x: x.get('id') == 'ingress', questions))
    questions = list(filter(lambda x: x.get('id') != 'ingress', questions))
    if ingress:
        questionglobal = etree.SubElement(out, 'global', {'type': 'compareNumeric'})
        questionglobal.text = ingress[0].text

    if questions:
        for index, question in enumerate(questions):
            attr = {'type': 'compareNumeric', 'key': str(index)}
            newquestion = etree.SubElement(out, 'question', attr)
            newtext = etree.SubElement(newquestion, 'text')
            newtext.text = question.get('question')
            newexp = etree.SubElement(newquestion, 'expression')
            newexp.text = question.text.strip()
    return etree.tostring(out, pretty_print=True, encoding="unicode")


def convert_recursive(path):
    for root, directories, filenames in os.walk(path):
        for filename in filenames:
            if filename == 'problem.xml':
                fullpath = os.path.join(root, filename)
                newpath = os.path.join(root, 'exercise.xml')
                with open(newpath, 'w') as f:
                    try:
                        f.write(convert(fullpath))
                    except Exception as e:
                        print(e)
                        print(fullpath)


def main(files):
    # if not files:
    #    print("No file given")
    #    return
    convert_recursive('./')


if __name__ == "__main__":
    main(sys.argv[1:])
