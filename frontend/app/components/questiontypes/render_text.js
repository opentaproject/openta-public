import React from "react"; // React specific import
import immutable from "immutable";
import DOMPurify from "dompurify";

const filterLanguage = (children, lang) => children.filter(
    item => item.getIn(["@attr", "lang"], undefined) === lang
  );

const dispatchElement = lang => element => {
  var itemDispatch = {
    text: itemjson => renderText(itemjson, dispatchElement(lang), lang),
    __text__: itemjson => renderText(itemjson, dispatchElement(lang), lang),
    alt: itemjson => renderText(itemjson, dispatchElement(lang), lang),
  };
  if (element.get("#name") in itemDispatch) return itemDispatch[element.get("#name")](element);
  else return null;
};

const renderText = (itemjson, dispatcher, lang) => {
  if (itemjson === undefined)
    return <span/>;
  var langFilteredJson = filterLanguage(itemjson.get("$children$", immutable.List([])), lang);
  if (dispatcher == null) {
    dispatcher = dispatchElement(lang);
  }
  var children = langFilteredJson.map(child => dispatcher(child)).toSeq();
  if (langFilteredJson.size > 0) {
    return <div key={"text" + itemjson.getIn(["$"], "")}>{children}</div>;
  } else {
    return (
      <div className="uk-clearfix" key={"text" + itemjson.getIn(["$"], "")}>
        <span dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(itemjson.getIn(["$"], "")) }} />
      </div>
    );
  }
};


export { renderText };