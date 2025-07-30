import Query from "../../queries/Query.js";
import ShapedObjectType from "./ShapedObjectType.js";

export default class VertexType extends ShapedObjectType {
  constructor(ecoreSync, model) {
    super(ecoreSync, model);
    this.shape = null;
    this.query = new Query(
      this.ecoreSync,
      this.model.get("alias"),
      this.model.get("queryStr"),
      this.model.get("queryTarget"),
      this.model.get("queryTargetAlias"),
    );
  }
}
