import * as d3 from 'd3'
import d3Tip from "d3-tip";

function groupBy(arr, property) {
    return arr.reduce(function (cur, obj) {
        var key = obj[property];
        if (!cur[key]) {
            cur[key] = [];
        }
        cur[key].push(obj);
        return cur;
    }, {});
}

export function drawHistoryCircle2(selection){
    let data = selection.data
    // console.log(data)
    data = data.sort((a, b)=>{
        return b.value-a.value
    })
    // console.log(data)
    let frame = d3.select(this).append('g').attr('id', selection.name)
    let colorScale = d3.scaleLinear().domain([0, 100]).range([0.75, 0.6])
    //添加提示框
    const tooltip = d3Tip()
        .attr('class', 'tips')
        .html(d=>{
            return `<div 
            style="width: auto;
            height: 20px;
            border-radius: 4px;
            background: #46484a;
            padding: 10px;
            position: relative;
            pointer-events: none;
            ">
            <div style="width: 0;height: 0;
            border-style: solid;
            position: absolute;
            left: 45%;
            bottom: -10px;
            border-width: 0px 10px 10px 10px;
            border-color: transparent transparent #46484a transparent;
            transform:rotate(180deg)
            "></div>
            ${d.name}:${d.value}</div>`
        })
    frame.call(tooltip)

    const x = d3.scaleBand()
        .range([0, 2 * Math.PI])    // X axis goes from 0 to 2pi = all around the circle. If I stop at 1Pi, it will be around a half circle
        .align(0)                  // This does nothing
        .domain(data.map(d => d.name)); // The domain of the X axis is the list of states.
    const y = d3.scaleRadial()
        .range([10, 30])   // Domain will be define later.
        .domain([0, 100]); // Domain of Y is from 0 to the max seen in the data

    //计算数据中每种类别的数量
    let typeGroup = data.reduce(function (acc, obj){
        const key = obj.type
        if(!acc[key])acc[key]=[]
        acc[key].push(obj)
        return acc;
    }, {})
    let typeKeys = Object.keys(typeGroup)
    let pieData = [typeKeys.length>0?typeGroup[typeKeys[0]].length:0,
        typeKeys.length>=2?typeGroup[typeKeys[1]].length:0,
        typeKeys.length==3?typeGroup[typeKeys[2]].length:0]
    // console.log(pieData)
    /****绘制内部饼图****/
        // 定义颜色比例尺
    var color = d3.scaleOrdinal()
            .range(["#98abc5", "#8a89a6", "#7b6888", "#6b486b"]);
    // 定义饼图生成器函数
    var pie = d3.pie()
        .value(function(d) { return d; });

    // 定义弧生成器函数
    var arc = d3.arc()
        .outerRadius(10-2) //设置饼图最外围的宽度
        .innerRadius(0);

    let arcs = frame.selectAll('arc')
        .data(pie(pieData))
        .enter()
        .append('g')

    arcs.append('path')
        .attr('d', arc)
        .style('fill', d=>{
            return color(d.index)
        })
        .attr('class', 'arc')

    //绘制外围的柱状图
    frame.selectAll("barPath")
        .data(data)
        .join("path")
        .attr("fill", (d)=>{
            let str = `hsl(10, 100%, ${Math.abs(colorScale(d.value))*100}%)`
            return str
        })
        .attr("d", d3.arc()     // imagine your doing a part of a donut plot
            .innerRadius(10)
            .outerRadius(d => y(d['value']))
            .startAngle(d => x(d.name))
            .endAngle(d => x(d.name) + x.bandwidth())
            .padAngle(0.1)
            .padRadius(15))
        .attr('class', 'bar')
        .on('mouseover', (e, d)=>tooltip.show(d, e.target))
        .on('mouseout', (e, d)=>{
            tooltip.destroy()
        })
    return frame.node()
}

export function DonutChart(data, {
    name = ([x]) => x,  // given d in data, returns the (ordinal) label
    value = ([, y]) => y, // given d in data, returns the (quantitative) value
    title, // given d in data, returns the title text
    width = 640, // outer width, in pixels
    height = 400, // outer height, in pixels
    innerRadius = Math.min(width, height) / 3, // inner radius of pie, in pixels (non-zero for donut)
    outerRadius = Math.min(width, height) / 2, // outer radius of pie, in pixels
    labelRadius = (innerRadius + outerRadius) / 2, // center radius of labels
    format = ",", // a format specifier for values (in the label)
    names, // array of names (the domain of the color scale)
    colors, // array of colors for names
    stroke = innerRadius > 0 ? "none" : "white", // stroke separating widths
    strokeWidth = 1, // width of stroke separating wedges
    strokeLinejoin = "round", // line join of stroke separating wedges
    padAngle = stroke === "none" ? 1 / outerRadius : 0, // angular separation between wedges
    svg=null
} = {}) {
    // Compute values.
    const N = d3.map(data, name);
    const V = d3.map(data, value);
    const I = d3.range(N.length).filter(i => !isNaN(V[i]));

    let tip = d3Tip()
      .attr("class", 'd3-tip')
      .offset(-10, 0)
      .html(function (d){
          return "<strong>d.name:</strong> <span style='color:red'>" + d.value + "</span>";
      })
    svg.call(tip)
    // Unique the names.
    if (names === undefined) names = N;
    names = new d3.InternSet(names);

    // Chose a default color scheme based on cardinality.
    if (colors === undefined) colors = d3.schemeSpectral[names.size];
    if (colors === undefined) colors = d3.quantize(t => d3.interpolateSpectral(t * 0.8 + 0.1), names.size);

    // Construct scales.
    const color = d3.scaleOrdinal(names, colors);

    // Compute titles.
    if (title === undefined) {
        const formatValue = d3.format(format);
        title = i => `${N[i]}\n${formatValue(V[i])}`;
    } else {
        const O = d3.map(data, d => d);
        const T = title;
        title = i => T(O[i], i, data);
    }

    // Construct arcs.
    const arcs = d3.pie().padAngle(padAngle).sort(null).value(i => V[i])(I);
    const arc = d3.arc().innerRadius(innerRadius).outerRadius(outerRadius);
    const arcLabel = d3.arc().innerRadius(labelRadius).outerRadius(labelRadius);
    svg.append("g")
        .attr("stroke", stroke)
        .attr("stroke-width", strokeWidth)
        .attr("stroke-linejoin", strokeLinejoin)
        .selectAll("path")
        .data(arcs)
        .join("path")
        .attr("fill", d => color(N[d.data]))
        .attr("d", arc)

      // svg.selectAll("path")
      //   .on('click', (e, d)=>{
      //       tip.show(d, e.target)})
      //   .on('mouseout', ()=>tip.destroy())
        // .append("title")
        // .text(d => title(d.data));

    // svg.append("g")
    //     .attr("font-family", "sans-serif")
    //     .attr("font-size", 10)
    //     .attr("text-anchor", "middle")
    //     .selectAll("text")
    //     .data(arcs)
    //     .join("text")
    //     .attr("transform", d => `translate(${arcLabel.centroid(d)})`)
    //     .selectAll("tspan")
    //     .data(d => {
    //         const lines = `${title(d.data)}`.split(/\n/);
    //         return (d.endAngle - d.startAngle) > 0.25 ? lines : lines.slice(0, 1);
    //     })
    //     .join("tspan")
    //     .attr("x", 0)
    //     .attr("y", (_, i) => `${i * 1.1}em`)
    //     .attr("font-weight", (_, i) => i ? null : "bold")
    //     .text(d => d);

}

