import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BuyStarsButton } from "@/components/BuyStarsButton";
import { BuyTonButton } from "@/components/BuyTonButton";
import type { Product } from "@/lib/api";

type Props = {
  product: Product;
};

export function ProductCard({ product }: Props) {
  return (
    <Card className="flex flex-col">
      <CardHeader>
        <div className="mb-2 text-3xl" aria-hidden>
          {product.icon}
        </div>
        <CardTitle>{product.name}</CardTitle>
        <CardDescription>{product.description}</CardDescription>
      </CardHeader>
      <CardContent className="mt-auto flex flex-col gap-3">
        <div className="flex flex-wrap gap-2">
          <Badge variant="default">{product.price}</Badge>
          <Badge variant="secondary">{product.stars}</Badge>
          <Badge variant="outline">{product.ton}</Badge>
        </div>
        <BuyStarsButton sku={product.sku} starsLabel={product.stars} />
        <BuyTonButton sku={product.sku} />
      </CardContent>
    </Card>
  );
}
