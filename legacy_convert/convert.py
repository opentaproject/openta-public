from lxml import etree
import sys


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

    add_converted_text(problem, out, "name", "exercisename")

    problemtext = problem.xpath("/problem/question/text/text()")
    if problemtext:
        exercisetext = etree.SubElement(out, 'exercisetext')
        exercisetext.text = problemtext[0].strip()
        add_converted_text(problem, exercisetext, "figure", "figure")

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
            newexp.text = question.text
    print(etree.tostring(out, pretty_print=True, encoding="unicode"))


def main(files):
    if not files:
        print("No file given")
        return
    convert(files[0])


if __name__ == "__main__":
    main(sys.argv[1:])
